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

function inicializarModalCliente() {
    const modal = document.getElementById('modal-cliente');
    const formulario = document.getElementById('formulario-cliente');
    const titulo = document.getElementById('modal-cliente-titulo');
    const contenedorError = document.getElementById('modal-cliente-error');

    if (!modal || !formulario) {
        return;
    }

    function ocultarError() {
        if (contenedorError) {
            contenedorError.hidden = true;
            contenedorError.textContent = '';
        }
    }

    function mostrarError(mensaje) {
        if (contenedorError) {
            contenedorError.textContent = mensaje;
            contenedorError.hidden = false;
        }

        const boton = formulario.querySelector('[data-cargando]');
        if (boton) {
            boton.disabled = false;
            if (boton.tagName === 'INPUT') {
                boton.value = 'Guardar';
            } else {
                boton.textContent = 'Guardar';
            }
        }
    }

    function abrirParaNuevo() {
        formulario.reset();
        ocultarError();
        formulario.action = '/clientes/nuevo';
        titulo.textContent = 'Nuevo cliente';
        modal.showModal();
    }

    function abrirParaEditar(boton) {
        formulario.reset();
        ocultarError();
        formulario.action = `/clientes/${boton.dataset.id}/editar`;
        formulario.elements['nombre'].value = boton.dataset.nombre || '';
        formulario.elements['email'].value = boton.dataset.email || '';
        formulario.elements['telefono'].value = boton.dataset.telefono || '';
        formulario.elements['empresa'].value = boton.dataset.empresa || '';
        formulario.elements['notas'].value = boton.dataset.notas || '';
        titulo.textContent = 'Editar cliente';
        modal.showModal();
    }

    document.querySelectorAll('.boton-nuevo-cliente').forEach(function (boton) {
        boton.addEventListener('click', abrirParaNuevo);
    });

    document.querySelectorAll('.boton-editar-cliente').forEach(function (boton) {
        boton.addEventListener('click', function () {
            abrirParaEditar(boton);
        });
    });

    const botonCancelar = document.getElementById('boton-cancelar-modal-cliente');
    const botonCerrar = document.getElementById('boton-cerrar-modal-cliente');
    [botonCancelar, botonCerrar].forEach(function (boton) {
        if (boton) {
            boton.addEventListener('click', function () {
                modal.close();
            });
        }
    });

    // Cerrar al hacer click afuera del contenido (sobre el backdrop).
    modal.addEventListener('click', function (evento) {
        if (evento.target === modal) {
            modal.close();
        }
    });

    // Envío por AJAX: así, si el servidor devuelve un error (email duplicado,
    // formato inválido, etc.), lo mostramos adentro del modal en vez de
    // navegar a la página completa del formulario.
    formulario.addEventListener('submit', function (evento) {
        evento.preventDefault();
        ocultarError();

        fetch(formulario.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(formulario)
        })
            .then(function (respuesta) {
                return respuesta.json();
            })
            .then(function (datos) {
                if (datos.exito) {
                    window.location.href = '/clientes';
                } else {
                    mostrarError(datos.error || 'Ocurrió un error al guardar el cliente.');
                }
            })
            .catch(function () {
                mostrarError('No se pudo conectar con el servidor. Probá de nuevo.');
            });
    });

    // Si alguien entra directo por /clientes/nuevo o /clientes/<id>/editar,
    // el servidor redirige acá con un parámetro en la URL y abrimos el modal solo.
    const parametros = new URLSearchParams(window.location.search);
    if (parametros.has('nuevo')) {
        abrirParaNuevo();
    } else if (parametros.has('editar')) {
        const botonCliente = document.querySelector(`.boton-editar-cliente[data-id="${parametros.get('editar')}"]`);
        if (botonCliente) {
            abrirParaEditar(botonCliente);
        }
    }

    if (parametros.has('nuevo') || parametros.has('editar')) {
        const url = new URL(window.location);
        url.searchParams.delete('nuevo');
        url.searchParams.delete('editar');
        window.history.replaceState({}, '', url);
    }
}

function inicializarModalProyecto() {
    const modal = document.getElementById('modal-proyecto');
    const formulario = document.getElementById('formulario-proyecto');
    const titulo = document.getElementById('modal-proyecto-titulo');
    const contenedorError = document.getElementById('modal-proyecto-error');

    if (!modal || !formulario) {
        return;
    }

    function ocultarError() {
        if (contenedorError) {
            contenedorError.hidden = true;
            contenedorError.textContent = '';
        }
    }

    function mostrarError(mensaje) {
        if (contenedorError) {
            contenedorError.textContent = mensaje;
            contenedorError.hidden = false;
        }

        const boton = formulario.querySelector('[data-cargando]');
        if (boton) {
            boton.disabled = false;
            if (boton.tagName === 'INPUT') {
                boton.value = 'Guardar';
            } else {
                boton.textContent = 'Guardar';
            }
        }
    }

    function abrirParaNuevo() {
        formulario.reset();
        ocultarError();
        formulario.action = '/proyectos/nuevo';
        titulo.textContent = 'Nuevo proyecto';
        modal.showModal();
    }

    function abrirParaEditar(boton) {
        formulario.reset();
        ocultarError();
        formulario.action = `/proyectos/${boton.dataset.id}/editar`;
        formulario.elements['titulo'].value = boton.dataset.titulo || '';
        formulario.elements['cliente_id'].value = boton.dataset.clienteId || '';
        formulario.elements['estado'].value = boton.dataset.estado || '';
        formulario.elements['fecha_entrega'].value = boton.dataset.fechaEntrega || '';
        titulo.textContent = 'Editar proyecto';
        modal.showModal();
    }

    document.querySelectorAll('.boton-nuevo-proyecto').forEach(function (boton) {
        boton.addEventListener('click', abrirParaNuevo);
    });

    document.querySelectorAll('.boton-editar-proyecto').forEach(function (boton) {
        boton.addEventListener('click', function () {
            abrirParaEditar(boton);
        });
    });

    const botonCancelar = document.getElementById('boton-cancelar-modal-proyecto');
    const botonCerrar = document.getElementById('boton-cerrar-modal-proyecto');
    [botonCancelar, botonCerrar].forEach(function (boton) {
        if (boton) {
            boton.addEventListener('click', function () {
                modal.close();
            });
        }
    });

    modal.addEventListener('click', function (evento) {
        if (evento.target === modal) {
            modal.close();
        }
    });

    formulario.addEventListener('submit', function (evento) {
        evento.preventDefault();
        ocultarError();

        fetch(formulario.action, {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: new FormData(formulario)
        })
            .then(function (respuesta) {
                return respuesta.json();
            })
            .then(function (datos) {
                if (datos.exito) {
                    window.location.href = '/proyectos';
                } else {
                    mostrarError(datos.error || 'Ocurrió un error al guardar el proyecto.');
                }
            })
            .catch(function () {
                mostrarError('No se pudo conectar con el servidor. Probá de nuevo.');
            });
    });

    const parametros = new URLSearchParams(window.location.search);
    if (parametros.has('nuevo')) {
        abrirParaNuevo();
    } else if (parametros.has('editar')) {
        const botonProyecto = document.querySelector(`.boton-editar-proyecto[data-id="${parametros.get('editar')}"]`);
        if (botonProyecto) {
            abrirParaEditar(botonProyecto);
        }
    }

    if (parametros.has('nuevo') || parametros.has('editar')) {
        const url = new URL(window.location);
        url.searchParams.delete('nuevo');
        url.searchParams.delete('editar');
        window.history.replaceState({}, '', url);
    }
}

function inicializarBuscadores() {
    inicializarBuscadorTabla('buscador-clientes', 'tabla-clientes', 'estado-sin-resultados', 'boton-limpiar-busqueda');
    inicializarBuscadorTabla('buscador-proyectos', 'tabla-proyectos', 'estado-sin-resultados-proyectos', 'boton-limpiar-busqueda-proyectos');
    inicializarBuscadorTabla('buscador-pagos', 'tabla-pagos', 'estado-sin-resultados-pagos', 'boton-limpiar-busqueda-pagos');
    inicializarBuscadorTabla('buscador-notas', 'tabla-notas', 'estado-sin-resultados-notas', 'boton-limpiar-busqueda-notas');
}

document.addEventListener('DOMContentLoaded', inicializarBotonTema);
document.addEventListener('DOMContentLoaded', inicializarBotonesCarga);
document.addEventListener('DOMContentLoaded', inicializarMenuMobile);
document.addEventListener('DOMContentLoaded', inicializarMenuUsuario);
document.addEventListener('DOMContentLoaded', inicializarBuscadores);
document.addEventListener('DOMContentLoaded', inicializarModalCliente);
document.addEventListener('DOMContentLoaded', inicializarModalProyecto);