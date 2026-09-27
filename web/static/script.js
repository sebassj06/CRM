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
    boton.textContent = esOscuro ? 'Modo claro' : 'Modo oscuro';
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

document.addEventListener('DOMContentLoaded', inicializarBotonTema);
document.addEventListener('DOMContentLoaded', inicializarBotonesCarga);
document.addEventListener('DOMContentLoaded', inicializarMenuMobile);