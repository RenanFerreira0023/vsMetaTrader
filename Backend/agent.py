import json
import logging
import inspect
import re
from typing import AsyncGenerator
from config import settings
from database import SessionLocal, User, Session as DBSession, Message
from rag import rag_engine
from prompts import get_system_prompt
from tools import TOOLS_REGISTRY, compile_meta_trader_code

logger = logging.getLogger("agent")

async def generate_mql_response(
    sess_uuid: str, 
    estagio0: str, 
    estagio1: str, 
    estagio2: str, 
    estagio3: str, 
    prompt_text: str, 
    client
) -> AsyncGenerator[str, None]:
    db = SessionLocal()
    try:
        # 1. Configurar Usuário e Sessão
        default_user = db.query(User).filter_by(username="mql_user").first()
        if not default_user:
            default_user = User(username="mql_user")
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
            
        db_session = db.query(DBSession).filter_by(session_uuid=sess_uuid).first()
        if not db_session:
            db_session = DBSession(user_id=default_user.id, session_uuid=sess_uuid)
            db.add(db_session)
            db.commit()
            db.refresh(db_session)

        # 2. Salvar Mensagem Atual do Usuário
        user_msg = Message(session_id=db_session.id, role="user", content=prompt_text)
        db.add(user_msg)
        db.commit()

        # 3. Resgatar Histórico Recente (últimas 10 mensagens)
        history = db.query(Message).filter_by(session_id=db_session.id).order_by(Message.created_at.desc()).limit(10).all()
        history.reverse() # Colocar de volta na ordem cronológica de leitura

        # 4. Buscar contexto RAG relevante baseado no Panorama Geral e Indicadores
        busca_rag = f"{estagio0} {estagio1}"
        rag_context = rag_engine.search_context(busca_rag, top_k=3)
        context_str = ""
        if rag_context:
            context_str = "ESTUDO DE CASO (ROBÔS SIMILARES NA SUA PASTA):\n"
            for chunk, meta in rag_context:
                context_str += f"Baseado em {meta['file']}:\n{chunk}\n\n"
        
        # 5. Montar lista de mensagens para o Ollama (Papéis Nativos)
        system_prompt = get_system_prompt()
        ollama_messages = [
            {'role': 'system', 'content': system_prompt}
        ]
        
        if context_str:
            ollama_messages.append({'role': 'system', 'content': context_str})

        # Adicionar histórico real
        for msg in history[:-1]:
            ollama_messages.append({'role': msg.role, 'content': msg.content})
        
        # Adicionar pergunta atual com reforço de regra (Sandwich Instruction)
        reforco_mql5 = (
            "\n\n⚠️ REGRAS CRÍTICAS DE EXECUÇÃO:\n"
            "1. VOCÊ ESTÁ NO MQL5. iMA() retorna um HANDLE (int). Use o exemplo validado abaixo.\n"
            "2. O MASTER TEMPLATE foi PRÉ-COMPILADO com SUCESSO (0 erros). Use-o como base absoluta.\n"
            "3. Use SEMPRE #include <Trade/Trade.mqh> no topo.\n"
        )
        ollama_messages.append({'role': 'user', 'content': prompt_text + reforco_mql5})

        # Injeção de Memória: Simula que a IA já validou o template e agora deve prosseguir
        simulated_tool_call = '{"name": "compile_meta_trader_code", "parameters": {"code": "codigo-resumido.mq5"}}'
        ollama_messages.append({'role': 'assistant', 'content': f"<tool_call>{simulated_tool_call}</tool_call>"})
        ollama_messages.append({'role': 'user', 'content': (
            "[Tool Execution Result (compile_meta_trader_code)]: Compilation Successful! No errors found.\n"
            "⚠️ INSTRUÇÃO: A base está validada. Agora, implemente a ESTRATÉGIA COMPLETA solicitada "
            "pelo usuário dentro desse código base, mantendo os includes e a estrutura funcional."
        )})

        logger.info(f"🚀 Enviando para Ollama ({settings.MODEL_NAME}). Mensagens: {len(ollama_messages)}")
        full_response = ""
        
        # 5. Agent Loop (ReAct) com limite de iterações
        iteration = 0
        max_iterations = settings.MAX_AGENT_ITERATIONS
        
        while iteration < max_iterations:
            iteration += 1
            buffer = ""
            in_tool = False
            tool_data = ""
            has_tool = False
            
            # --- Geração via Ollama ---
            try:
                logger.info(f"🤖 Iniciando geração - Iteração {iteration}...")
                
                # Limpeza de histórico para evitar confusão em loops longos
                if iteration > 5:
                    ollama_messages = [ollama_messages[0], ollama_messages[1]] + ollama_messages[-8:]
                    logger.info(f"🧹 Histórico podado para a Iteração {iteration} (Preservando contexto crítico)...")
                
                stream = await client.chat(
                    model=settings.MODEL_NAME,
                    messages=ollama_messages,
                    stream=True,
                    options={
                        'temperature': settings.TEMPERATURE,
                        'num_predict': settings.MAX_TOKENS,
                    }
                )

                in_thinking = False
                
                async for chunk in stream:
                    token = chunk['message']['content']
                    full_response += token
                    print(token, end="", flush=True)
                    buffer += token

                    # Lógica de ocultação de pensamento
                    if "<think>" in buffer and not in_thinking:
                        parts = buffer.split("<think>")
                        if parts[0]:
                            yield parts[0]
                        in_thinking = True
                        buffer = parts[1] if len(parts) > 1 else ""
                    
                    if in_thinking:
                        if "</think>" in buffer:
                            parts = buffer.split("</think>")
                            in_thinking = False
                            buffer = parts[1] if len(parts) > 1 else ""
                        else:
                            continue

                    # Lógica de intercepção de ferramentas
                    if not in_tool:
                        if "<tool_call>" in buffer:
                            parts = buffer.split("<tool_call>")
                            if parts[0]:
                                yield parts[0]
                            in_tool = True
                            buffer = parts[1] if len(parts) > 1 else ""
                            has_tool = True
                        else:
                            idx = buffer.rfind("<")
                            if idx != -1:
                                chunk_to_send = buffer[:idx]
                                if chunk_to_send:
                                    yield chunk_to_send
                                buffer = buffer[idx:]
                                if not "<tool_call>".startswith(buffer) and not "<think>".startswith(buffer):
                                    yield buffer
                                    buffer = ""
                            else:
                                yield buffer
                                buffer = ""
                    else:
                        if "</tool_call>" in buffer:
                            parts = buffer.split("</tool_call>")
                            tool_data = parts[0]
                            break 
                        else:
                            tool_data = buffer

            except Exception as e:
                logger.error(f"Erro na geração Ollama: {e}")
                yield f"\nErro na geração: {str(e)}"
                break
                            
            if not in_tool and buffer:
                yield buffer

            # Avaliar se o loop de LLM invocou uma ferramenta validada
            if has_tool:
                t_name = "unknown"
                try:
                    clean_json_str = tool_data.strip()
                    tool_exec = json.loads(clean_json_str)
                    t_name = tool_exec.get("name", "unknown")
                    t_params = tool_exec.get("parameters", {})
                    
                    logger.info(f"🛠️ Ferramenta acionada: {t_name} | Params: {t_params}")
                    
                    if t_name in TOOLS_REGISTRY:
                        if t_name == "read_url_content":
                            logger.info(f"🔍 IA consultando documentação oficial: {t_params.get('Url')}")
                            
                        if t_name == "lookup_mql_error":
                            logger.info(f"🔍 IA consultando base de dados local para o erro: {t_params.get('error_code')}")
                            
                        res = TOOLS_REGISTRY[t_name](**t_params)
                        if inspect.iscoroutine(res):
                            tool_result = await res
                        else:
                            tool_result = res
                    else:
                        tool_result = f"Error: A ferramenta '{t_name}' não existe."
                        
                except Exception as e:
                    logger.error(f"Erro ao parsear/executar a ferramenta: {e}")
                    tool_result = f"Error interpreting tool parameters: {str(e)}. Make sure to respond only with standard JSON format."
                    
                msg_to_add = f"\n[Tool Execution Result ({t_name})]: {tool_result}"
                ollama_messages.append({'role': 'assistant', 'content': f"<tool_call>{tool_data}</tool_call>"})
                ollama_messages.append({'role': 'user', 'content': f"{msg_to_add}\n⚠️ INSTRUÇÃO: Prossiga IMEDIATAMENTE com a implementação da estratégia solicitada, usando as informações acima se necessário."})
                
                full_response += f"\n[System Log: executed {t_name} -> {tool_result}]\n"
            else:
                # Extrair explicação e logs
                explanation = re.sub(r"```[\s\S]+?```", "", full_response).strip()
                if explanation:
                    logger.info(f"🤖 O QUE A IA ENTENDEU DO ERRO:\n{explanation[:300]}...")
                    
                mql_blocks = re.findall(r"```(?:mql5|mql|cpp)\n([\s\S]+?)```", full_response)
                if mql_blocks:
                    mql_code = mql_blocks[-1]
                    
                    if "```cpp" in full_response:
                        logger.warning("⚠️ IA usou a tag ```cpp em vez de ```mql5. Corrigindo mentalidade...")
                        ollama_messages.append({'role': 'user', 'content': "⚠️ AVISO: Você usou a tag ```cpp. Use SEMPRE ```mql5 para código MetaTrader 5. Não repita esse erro."})
                
                if not mql_blocks:
                    generic_blocks = re.findall(r"```(?!\w*json)\w*\n([\s\S]+?)```", full_response)
                    if generic_blocks:
                        mql_blocks = [generic_blocks[-1]]

                if mql_blocks:
                    mql_code = mql_blocks[-1]
                    
                    if "Compilation Successful" not in full_response or iteration == 1:
                        logger.info(f"⚠️ Código MQL detectado (Iteração {iteration}). Forçando validação...")
                        
                        if len(mql_code.strip()) < 150 or "OnTick" not in mql_code:
                            logger.warning("⚠️ IA tentou compilar código incompleto/vazio. Recusando...")
                            msg_to_add = (
                                "\n⚠️ ERRO: O código que você enviou está incompleto ou vazio demais. "
                                "É OBRIGATÓRIO incluir toda a estrutura (Includes, OnInit, OnTick, OnDeinit). "
                                "Escreva o código completo agora."
                            )
                            ollama_messages.append({'role': 'user', 'content': msg_to_add})
                            continue

                        if "#include <Trade/Trade.mqh>" not in mql_code:
                            logger.warning("⚠️ IA errou o caminho do include Trade.mqh. Recusando...")
                            msg_to_add = (
                                "\n⚠️ ERRO CRÍTICO DE INCLUDE: Você esqueceu ou errou o include obrigatório.\n"
                                "Use EXATAMENTE: #include <Trade/Trade.mqh>\n"
                                "Sem isso, a classe CTrade não será encontrada. Corrija isso agora."
                            )
                            ollama_messages.append({'role': 'user', 'content': msg_to_add})
                            continue

                        mql4_forbidden = ["OrderSend", "OrderClose", "Symbol()", "OP_BUY", "OP_SELL", "MarketInfo", "MarketPosition", "OnStart()"]
                        found_forbidden = [f for f in mql4_forbidden if f in mql_code]
                        if found_forbidden:
                            logger.warning(f"⚠️ IA usou termos proibidos do MQL4: {found_forbidden}. Recusando...")
                            msg_to_add = (
                                f"\n❌ ERRO DE VERSÃO: Você usou funções do MQL4 (MetaTrader 4): {found_forbidden}.\n"
                                "Isso é PROIBIDO! Você deve usar EXCLUSIVAMENTE MQL5.\n"
                                "- Em vez de OrderSend, use `trade.Buy()` ou `trade.Sell()`.\n"
                                "- Em vez de Symbol(), use `_Symbol`.\n"
                                "- Em vez de OnStart, use `OnTick`.\n"
                                "CORRIJA O CÓDIGO AGORA."
                            )
                            ollama_messages.append({'role': 'user', 'content': msg_to_add})
                            continue

                        comp_result = compile_meta_trader_code(mql_code)
                        
                        yield f"\n--- LOG DE COMPILAÇÃO ---\n{comp_result}\n--------------------------\n"
                        
                        is_success = "Compilation Successful" in comp_result
                        if is_success:
                            full_response += f"\n\n✅ [Compilation Successful! No errors found.]\n"
                            ontick_content = re.search(r"void\s+OnTick\s*\(\s*\)\s*\{([\s\S]*?)\}", mql_code)
                            has_real_logic = False
                            if ontick_content:
                                logic_text = ontick_content.group(1).strip()
                                clean_logic = re.sub(r"//.*|/\*[\s\S]*?\*/", "", logic_text).strip()
                                if len(clean_logic) > 10:
                                    has_real_logic = True

                            if not has_real_logic:
                                original_goal = prompt_text[:300] + "..." if len(prompt_text) > 300 else prompt_text
                                msg_to_add = (
                                    f"⚠️ O código COMPILOU COM SUCESSO, mas o OnTick está vazio ou incompleto!\n"
                                    f"VOCÊ DEVE implementar a lógica da estratégia solicitada: [{original_goal}]\n"
                                    "Não peça mais informações, use o que o usuário já forneceu no início."
                                )
                                ollama_messages.append({'role': 'user', 'content': msg_to_add})
                                logger.info("ℹ️ Código compilou mas OnTick está vazio. Re-injetando objetivo...")
                                continue 
                        else:
                            all_lines = str(comp_result).split('\n')
                            useful_lines = [l for l in all_lines if "error " in l.lower() or "warning " in l.lower() or "information: compiling" in l.lower()]
                            
                            if not useful_lines:
                                useful_lines = all_lines[:15]
                            
                            tool_result_sliced = "\n".join(useful_lines[:15])
                            logger.info(f"⚠️ Erro de compilação detectado. Filtrando log para focar nos erros reais...")
                            
                            hints = [line for line in all_lines if "info  " in line or "built-in:" in line]
                            hint_text = "\n💡 DICA DO COMPILADOR:\n" + "\n".join(hints[:5]) if hints else ""
                            
                            msg_to_add = (
                                f"\n[System Auto-Validation - COMPILATION ERRORS]:\n{tool_result_sliced}\n"
                                f"{hint_text}\n"
                                "⚠️ PROTOCOLO OBRIGATÓRIO: Identifique o CÓDIGO do erro acima (ex: error 256) "
                                "e use a ferramenta 'lookup_mql_error' para entender o problema antes de tentar corrigir. NÃO adivinhe a solução."
                            )
                            ollama_messages.append({'role': 'user', 'content': msg_to_add})
                            full_response += f"\n[System Log: auto-validation check phase {iteration} -> {comp_result}]\n"
                            continue
                
                if iteration == 1 and not has_tool:
                    mql_blocks = re.findall(r"```(?:mql5|mql)\n([\s\S]+?)```", full_response)
                    if not mql_blocks and len(full_response) < 500:
                        logger.warning("⚠️ IA tentou ser preguiçosa (não gerou código). Forçando geração...")
                        ollama_messages.append({'role': 'assistant', 'content': full_response})
                        ollama_messages.append({
                            'role': 'user', 
                            'content': "ERRO: Você não forneceu o código MQL5! Não dê instruções para eu fazer, FAÇA VOCÊ MESMO. Escreva o código completo da estratégia AGORA dentro do padrão MASTER TEMPLATE."
                        })
                        continue

                break

        # 6. Salvar resposta no banco ao finalizar o stream
        assistant_msg = Message(session_id=db_session.id, role="assistant", content=full_response)
        db.add(assistant_msg)
        db.commit()

    except Exception as e:
        logger.error(f"Erro durante gerador de resposta: {e}")
        db.rollback()
    finally:
        db.close()
