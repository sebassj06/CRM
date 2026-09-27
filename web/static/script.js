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

document.addEventListener('DOMContentLoaded', actualizarTextoBoton);