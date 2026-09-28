function alternarTema() {
    const esOscuro = document.documentElement.getAttribute('data-theme') === 'dark';

    if (esOscuro) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('tema', 'claro');
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('tema', 'oscuro');
    }

    actualizarTextoBoton();
}

function actualizarTextoBoton() {
    const boton = document.getElementById('boton-tema');
    if (!boton) {
        return;
    }
    const esOscuro = document.documentElement.getAttribute('data-theme') === 'dark';
    const texto = esOscuro ? 'Modo claro' : 'Modo oscuro';

    // Si el botón tiene un ícono adentro (dropdown de usuario), solo actualizamos
    // el texto del span interno para no borrar el SVG con textContent.
    const spanTexto = document.getElementById('texto-tema');
    if (spanTexto) {
        spanTexto.textContent = texto;
    } else {
        boton.textContent = texto;
    }
}

function inicializarBotonTema() {
    actualizarTextoBoton();

    const boton = document.getElementById('boton-tema');
    if (boton) {
        boton.addEventListener('click', alternarTema);
    }
}

function inicializarBotonesCarga() {
    document.querySelectorAll('form').forEach(function (formulario) {
        formulario.addEventListener('submit', function () {
            const boton = formulario.querySelector('[data-cargando]');
            if (!boton) {
                return;
            }
            boton.disabled = true;
            if (boton.tagName === 'INPUT') {
                boton.value = boton.dataset.cargando;
            } else {
                boton.textContent = boton.dataset.cargando;
            }
        });
    });
}

function inicializarMenuMobile() {
    const boton = document.getElementById('boton-menu');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('overlay-menu');

    if (!boton || !sidebar || !overlay) {
        return;
    }

    function cerrarMenu() {
        sidebar.classList.remove('abierto');
        overlay.classList.remove('visible');
    }

    boton.addEventListener('click', function () {
        sidebar.classList.toggle('abierto');
        overlay.classList.toggle('visible');
    });

    overlay.addEventListener('click', cerrarMenu);
}

function inicializarMenuUsuario() {
    const contenedor = document.querySelector('.menu-usuario');
    const boton = document.getElementById('boton-usuario');

    if (!contenedor || !boton) {
        return;
    }

    function cerrarMenu() {
        contenedor.classList.remove('abierto');
        boton.setAttribute('aria-expanded', 'false');
    }

    boton.addEventListener('click', function (evento) {
        evento.stopPropagation();
        const abierto = contenedor.classList.toggle('abierto');
        boton.setAttribute('aria-expanded', abierto ? 'true' : 'false');
    });

    document.addEventListener('click', function (evento) {
        if (!contenedor.contains(evento.target)) {
            cerrarMenu();
        }
    });

    document.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape') {
            cerrarMenu();
        }
    });
}

function inicializarBuscadorTabla(idInput, idTabla, idSinResultados, idBotonLimpiar) {
    const input = document.getElementById(idInput);
    const tabla = document.getElementById(idTabla);
    const estadoSinResultados = document.getElementById(idSinResultados);
    const botonLimpiar = document.getElementById(idBotonLimpiar);

    if (!input || !tabla) {
        return;
    }

    const filas = tabla.querySelectorAll('tbody tr');

    function filtrar() {
        const termino = input.value.trim().toLowerCase();
        let visibles = 0;

        filas.forEach(function (fila) {
            const texto = fila.dataset.busqueda || fila.textContent.toLowerCase();
            const coincide = texto.includes(termino);
            fila.style.display = coincide ? '' : 'none';
            if (coincide) {
                visibles++;
            }
        });

        tabla.hidden = visibles === 0;
        if (estadoSinResultados) {
            estadoSinResultados.hidden = visibles !== 0;
        }
    }

    input.addEventListener('input', filtrar);

    if (botonLimpiar) {
        botonLimpiar.addEventListener('click', function () {
            input.value = '';
            filtrar();
            input.focus();
        });
    }
}

function inicializarBuscadores() {
    inicializarBuscadorTabla('buscador-clientes', 'tabla-clientes', 'estado-sin-resultados', 'boton-limpiar-busqueda');
    inicializarBuscadorTabla('buscador-proyectos', 'tabla-proyectos', 'estado-sin-resultados-proyectos', 'boton-limpiar-busqueda-proyectos');
}

document.addEventListener('DOMContentLoaded', inicializarBotonTema);
document.addEventListener('DOMContentLoaded', inicializarBotonesCarga);
document.addEventListener('DOMContentLoaded', inicializarMenuMobile);
document.addEventListener('DOMContentLoaded', inicializarMenuUsuario);
document.addEventListener('DOMContentLoaded', inicializarBuscadores);