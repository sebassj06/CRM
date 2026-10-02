POR_PAGINA = 25


def normalizar_pagina(pagina):
    try:
        pagina = int(pagina)
    except (TypeError, ValueError):
        pagina = 1
    return max(1, pagina)


def total_paginas(total_registros, por_pagina=POR_PAGINA):
    return max(1, (total_registros + por_pagina - 1) // por_pagina)
