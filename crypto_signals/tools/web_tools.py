def price_direction(crypto):
    result = {}

    recomendation_indicator = crypto['ema'] + crypto['st'] + crypto['MACD'] + \
                              crypto['RSI'] + crypto['stoch']
    if recomendation_indicator <= -4:
        result['result'] = "Высокая SHORT"
        result['result_class'] = 'text-danger'
    elif -3 <= recomendation_indicator <= -2:
        result['result'] = "SHORT"
        result['result_class'] = 'text-danger'
    elif -1 <= recomendation_indicator <= 1:
        result['result'] = "Боковое"
        result['result_class'] = 'text-warning'
    elif 2 <= recomendation_indicator <= 3:
        result['result'] = "LONG"
        result['result_class'] = 'text-success'
    elif recomendation_indicator >= 4:
        result['result'] = "Высокая LONG"
        result['result_class'] = 'text-success'

    return result