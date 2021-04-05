def vizParam(bands, buffer, image, satellite):
    
    if not bands: #didn't find images for the sample
        return {}

    return {
        'min': 0,
        'max': 3000,
        'bands': bands
    }