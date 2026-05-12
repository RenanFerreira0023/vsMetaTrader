"""
mql5_sanitizer.py
Auto-sanitizador de código MQL4 → MQL5.
Corrige automaticamente chamadas incorretas de indicadores antes de compilar.

Assinaturas MQL5 oficiais (6 parâmetros base: symbol, timeframe, ...params, applied_price):
  iMA(symbol, tf, period, shift, method, applied_price)                          → 6 params
  iRSI(symbol, tf, period, applied_price)                                        → 4 params
  iMACD(symbol, tf, fast, slow, signal, applied_price)                           → 6 params
  iBands(symbol, tf, period, bands_shift, deviation, applied_price)              → 6 params
  iStochastic(symbol, tf, Kperiod, Dperiod, slowing, method, applied_price)     → 7 params
  iCCI(symbol, tf, period, applied_price)                                        → 4 params
  iATR(symbol, tf, period)                                                       → 3 params
  iADX(symbol, tf, period)                                                       → 3 params
  iADXWilder(symbol, tf, period)                                                 → 3 params
  iAlligator(symbol, tf, jaw_p, jaw_s, teeth_p, teeth_s, lips_p, lips_s, method, applied_price) → 10 params
  iAO(symbol, tf)                                                                → 2 params
  iAC(symbol, tf)                                                                → 2 params
  iMomentum(symbol, tf, period, applied_price)                                  → 4 params
  iMFI(symbol, tf, period, volume_type)                                          → 4 params
  iOBV(symbol, tf, volume_type)                                                  → 3 params
  iSAR(symbol, tf, step, max)                                                    → 4 params
  iWPR(symbol, tf, period)                                                       → 3 params
  iStdDev(symbol, tf, period, shift, method, applied_price)                     → 6 params
  iEnvelopes(symbol, tf, period, shift, method, applied_price, deviation)       → 7 params
  iForce(symbol, tf, period, method, applied_price)                              → 5 params
  iBearsPower(symbol, tf, period)                                                → 3 params
  iBullsPower(symbol, tf, period)                                                → 3 params
  iChaikin(symbol, tf, fast, slow, method, volume_type)                         → 6 params
  iDeMarker(symbol, tf, period)                                                  → 3 params
  iRVI(symbol, tf, period)                                                       → 3 params
  iAMA(symbol, tf, period, fast, slow, shift, applied_price)                    → 7 params
  iDEMA(symbol, tf, period, shift, applied_price)                               → 5 params
  iTEMA(symbol, tf, period, shift, applied_price)                               → 5 params
  iFrAMA(symbol, tf, period, shift, applied_price)                              → 5 params
  iVIDyA(symbol, tf, period, smooth, shift, applied_price)                      → 6 params
  iVolumes(symbol, tf, volume_type)                                              → 3 params
  iGator(symbol, tf, jaw_p, jaw_s, teeth_p, teeth_s, lips_p, lips_s, method, applied_price) → 10 params
  iIchimoku(symbol, tf, tenkan, kijun, senkou)                                  → 5 params
  iOsMA(symbol, tf, fast, slow, signal, applied_price)                          → 6 params
  iTriX(symbol, tf, period, applied_price)                                      → 4 params
  iBWMFI(symbol, tf, volume_type)                                               → 3 params
  iFractals(symbol, tf)                                                          → 2 params
  iAD(symbol, tf, volume_type)                                                   → 3 params
"""

import re

# Padrão reutilizável para o primeiro argumento (symbol)
_SYM = r'(?:NULL|_Symbol|"[^"]*"|\w+)'
# Padrão reutilizável para timeframe
_TF  = r'(?:\d+|_Period|PERIOD_[A-Z0-9]+)'
# Padrão para applied_price
_AP  = r'(?:PRICE_[A-Z]+|\d+)'
# Padrão para ma_method
_MM  = r'(?:MODE_[A-Z]+|\d+)'
# Padrão para volume_type
_VT  = r'(?:VOLUME_[A-Z]+|\d+)'
# Padrão genérico de argumento (não-vírgula, não-parêntese aninhado simples)
_ARG = r'[^,)]+'

# ─────────────────────────────────────────────────────────────────────────────
# Tabela de correções:
# Cada entrada: (nome_funcao, regex_pattern, replacement_string)
# O regex captura chamadas com parâmetros "extras" MQL4 (geralmente o shift
# extra no final) e normaliza para a assinatura MQL5 correta.
# ─────────────────────────────────────────────────────────────────────────────

MQL4_INDICATOR_FIXES = [
    # iMA(sym, tf, period, shift, method, applied_price, EXTRA_BAR_SHIFT)
    # MQL5: iMA(sym, tf, period, shift, method, applied_price) — 6 params
    (
        'iMA',
        re.compile(
            rf'iMA\s*\(\s*({_SYM})\s*,\s*({_TF})\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*({_MM})\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iMA(_Symbol, _Period, \3, \4, \5, \6)'
    ),

    # iRSI(sym, tf, period, applied_price, EXTRA_SHIFT)
    # MQL5: iRSI(sym, tf, period, applied_price) — 4 params
    (
        'iRSI',
        re.compile(
            rf'iRSI\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iRSI(_Symbol, _Period, \1, \2)'
    ),

    # iMACD(sym, tf, fast, slow, signal, applied_price, EXTRA)
    # MQL5: iMACD(sym, tf, fast, slow, signal, applied_price) — 6 params
    (
        'iMACD',
        re.compile(
            rf'iMACD\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iMACD(_Symbol, _Period, \1, \2, \3, \4)'
    ),

    # iBands(sym, tf, period, bands_shift, deviation, applied_price, EXTRA)
    # MQL5: iBands(sym, tf, period, bands_shift, deviation, applied_price) — 6 params
    (
        'iBands',
        re.compile(
            rf'iBands\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iBands(_Symbol, _Period, \1, \2, \3, \4)'
    ),

    # iStochastic(sym, tf, Kperiod, Dperiod, slowing, method, applied_price, EXTRA)
    # MQL5: iStochastic(sym, tf, Kperiod, Dperiod, slowing, method, applied_price) — 7 params
    (
        'iStochastic',
        re.compile(
            rf'iStochastic\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*({_MM})\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iStochastic(_Symbol, _Period, \1, \2, \3, \4, \5)'
    ),

    # iCCI(sym, tf, period, applied_price, EXTRA)
    # MQL5: iCCI(sym, tf, period, applied_price) — 4 params
    (
        'iCCI',
        re.compile(
            rf'iCCI\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iCCI(_Symbol, _Period, \1, \2)'
    ),

    # iATR(sym, tf, period, EXTRA)
    # MQL5: iATR(sym, tf, period) — 3 params
    (
        'iATR',
        re.compile(
            rf'iATR\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*\d+\s*\)',
        ),
        r'iATR(_Symbol, _Period, \1)'
    ),

    # iADX / iADXWilder(sym, tf, period, EXTRA)
    # MQL5: iADX(sym, tf, period) — 3 params
    (
        'iADX',
        re.compile(
            rf'iADX\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*(?:,\s*\d+\s*)?\)',
        ),
        r'iADX(_Symbol, _Period, \1)'
    ),
    (
        'iADXWilder',
        re.compile(
            rf'iADXWilder\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*(?:,\s*\d+\s*)?\)',
        ),
        r'iADXWilder(_Symbol, _Period, \1)'
    ),

    # iSAR(sym, tf, step, max, EXTRA)
    # MQL5: iSAR(sym, tf, step, max) — 4 params
    (
        'iSAR',
        re.compile(
            rf'iSAR\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*\d+\s*\)',
        ),
        r'iSAR(_Symbol, _Period, \1, \2)'
    ),

    # iWPR(sym, tf, period, EXTRA)
    # MQL5: iWPR(sym, tf, period) — 3 params
    (
        'iWPR',
        re.compile(
            rf'iWPR\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*(?:,\s*\d+\s*)?\)',
        ),
        r'iWPR(_Symbol, _Period, \1)'
    ),

    # iMomentum(sym, tf, period, applied_price, EXTRA)
    # MQL5: iMomentum(sym, tf, period, applied_price) — 4 params
    (
        'iMomentum',
        re.compile(
            rf'iMomentum\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iMomentum(_Symbol, _Period, \1, \2)'
    ),

    # iDeMarker(sym, tf, period, EXTRA)
    # MQL5: iDeMarker(sym, tf, period) — 3 params
    (
        'iDeMarker',
        re.compile(
            rf'iDeMarker\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*(?:,\s*\d+\s*)?\)',
        ),
        r'iDeMarker(_Symbol, _Period, \1)'
    ),

    # iBearsPower / iBullsPower(sym, tf, period, EXTRA)
    # MQL5: iBearsPower(sym, tf, period) — 3 params
    (
        'iBearsPower',
        re.compile(
            rf'iBearsPower\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*(?:,\s*\d+\s*)?\)',
        ),
        r'iBearsPower(_Symbol, _Period, \1)'
    ),
    (
        'iBullsPower',
        re.compile(
            rf'iBullsPower\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*(?:,\s*\d+\s*)?\)',
        ),
        r'iBullsPower(_Symbol, _Period, \1)'
    ),

    # iRVI(sym, tf, period, EXTRA)
    # MQL5: iRVI(sym, tf, period) — 3 params
    (
        'iRVI',
        re.compile(
            rf'iRVI\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*(?:,\s*\d+\s*)?\)',
        ),
        r'iRVI(_Symbol, _Period, \1)'
    ),

    # iStdDev(sym, tf, period, shift, method, applied_price, EXTRA)
    # MQL5: iStdDev(sym, tf, period, shift, method, applied_price) — 6 params
    (
        'iStdDev',
        re.compile(
            rf'iStdDev\s*\(\s*{_SYM}\s*,\s*{_TF}\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*({_MM})\s*,\s*({_AP})\s*,\s*\d+\s*\)',
        ),
        r'iStdDev(_Symbol, _Period, \1, \2, \3, \4)'
    ),
]

# ─────────────────────────────────────────────────────────────────────────────
# Correções de operações de trading (MQL4 → CTrade MQL5)
# ─────────────────────────────────────────────────────────────────────────────

MQL4_TRADE_FIXES = [
    # OrderSend OP_BUY → trade.Buy
    (re.compile(r'OrderSend\s*\([^)]*OP_BUY[^)]*\)\s*;?'), 'trade.Buy(INITIAL_LOT, _Symbol);'),
    # OrderSend OP_SELL → trade.Sell
    (re.compile(r'OrderSend\s*\([^)]*OP_SELL[^)]*\)\s*;?'), 'trade.Sell(INITIAL_LOT, _Symbol);'),
    # OrderClose → PositionClose
    (re.compile(r'OrderClose\s*\([^)]*\)\s*;?'), 'trade.PositionClose(_Symbol);'),
    # Symbol() → _Symbol
    (re.compile(r'\bSymbol\s*\(\s*\)'), '_Symbol'),
    # LotSize / Lots → INITIAL_LOT
    (re.compile(r'\bLotSize\b'), 'INITIAL_LOT'),
    (re.compile(r'\bLots\b(?!\s*=\s*\d)'), 'INITIAL_LOT'),
    # Close[N] → iClose(_Symbol, _Period, N)
    (re.compile(r'\bClose\s*\[\s*(\d+)\s*\]'), r'iClose(_Symbol, _Period, \1)'),
    # Open[N] → iOpen
    (re.compile(r'\bOpen\s*\[\s*(\d+)\s*\]'), r'iOpen(_Symbol, _Period, \1)'),
    # High[N] → iHigh
    (re.compile(r'\bHigh\s*\[\s*(\d+)\s*\]'), r'iHigh(_Symbol, _Period, \1)'),
    # Low[N] → iLow
    (re.compile(r'\bLow\s*\[\s*(\d+)\s*\]'), r'iLow(_Symbol, _Period, \1)'),
    # Volume[N] → iVolume
    (re.compile(r'\bVolume\s*\[\s*(\d+)\s*\]'), r'iVolume(_Symbol, _Period, \1)'),
]


def sanitize(code: str) -> str:
    """Aplica todas as correções MQL4→MQL5 no código fornecido."""
    # 1. Correções de trading
    for pattern, replacement in MQL4_TRADE_FIXES:
        code = pattern.sub(replacement, code)

    # 2. Correções de indicadores (7+ params → params corretos)
    for name, pattern, replacement in MQL4_INDICATOR_FIXES:
        code = pattern.sub(replacement, code)

    return code
