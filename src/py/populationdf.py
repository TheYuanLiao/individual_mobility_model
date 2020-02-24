def rescale(populationdf):
    populationdf['population_normal'] = populationdf['population'] / populationdf['population'].max()
    populationdf['population_pow'] = populationdf['population_normal'] ** 2
    return populationdf
