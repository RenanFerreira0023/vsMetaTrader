import base64

def decode_base64(file: str) -> str:
    try:
        if "," in file:
            header, encoded = file.split(",", 1)
        else:
            encoded = file
        
        decoded_bytes = base64.b64decode(encoded)
        # Tenta ler como texto, se falhar mantém como bytes
        try:
            return decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return decoded_bytes
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao decodificar arquivo base64: {str(e)}")