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

function inicializarMenusDesplegables() {
    // Maneja cualquier menú desplegable del topbar (usuario, notificaciones, ...)
    // que comparta la clase .menu-desplegable con un botón [aria-haspopup="true"]
    // adentro. Abrir uno cierra los demás.
    document.querySelectorAll('.menu-desplegable').forEach(function (contenedor) {
        const boton = contenedor.querySelector('[aria-haspopup="true"]');
        if (!boton) {
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

            if (abierto) {
                document.querySelectorAll('.menu-desplegable.abierto').forEach(function (otro) {
                    if (otro !== contenedor) {
                        otro.classList.remove('abierto');
                        const otroBoton = otro.querySelector('[aria-haspopup="true"]');
                        if (otroBoton) {
                            otroBoton.setAttribute('aria-expanded', 'false');
                        }
                    }
                });
            }
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
    });
}

function inicializarBuscadorTabla(idInput, idTabla, idSinResultados, idBotonLimpiar) {
    const input = document.getElementById(idInput);
    const tabla = document.getElementById(idTabla);
    const estadoSinResultados = document.getElementById(idSinResultados);
    const botonLimpiar = document.getElementById(idBotonLimpiar);
    const paginacion = tabla ? tabla.parentElement.querySelector('.paginacion') : null;

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
        // La búsqueda local solo filtra lo que ya está en esta página — si hay
        // más páginas, la paginación no tiene sentido mientras se busca (para
        // buscar en todos los registros está el buscador global del topbar).
        if (paginacion) {
            paginacion.hidden = termino !== '';
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
    const selectPrefijo = document.getElementById('modal-telefono-prefijo');
    const inputNumero = document.getElementById('modal-telefono-numero');
    const inputTelefonoOculto = document.getElementById('modal-telefono');

    if (!modal || !formulario) {
        return;
    }

    function actualizarLongitudTelefono() {
        if (!selectPrefijo || !inputNumero) {
            return;
        }
        const opcion = selectPrefijo.options[selectPrefijo.selectedIndex];
        const longitud = opcion ? opcion.dataset.longitud : null;
        if (longitud) {
            inputNumero.setAttribute('maxlength', longitud);
            inputNumero.setAttribute('minlength', longitud);
            inputNumero.setAttribute('placeholder', `Ej: ${'5'.repeat(Number(longitud))}`);
        }
    }

    function combinarTelefono() {
        if (!selectPrefijo || !inputNumero || !inputTelefonoOculto) {
            return;
        }
        const numero = inputNumero.value.trim();
        inputTelefonoOculto.value = numero ? `${selectPrefijo.value} ${numero}` : '';
    }

    // Separa un teléfono guardado ("+54 91112345678") en prefijo + número
    // para precargar los dos campos visibles al editar. Si no reconocemos
    // el prefijo (por ejemplo, quedó cargado como texto libre antes de este
    // cambio), dejamos todo el valor en el campo de número para no perder
    // el dato.
    function cargarTelefono(valorGuardado) {
        if (!selectPrefijo || !inputNumero) {
            return;
        }
        selectPrefijo.selectedIndex = 0;
        inputNumero.value = '';
        if (!valorGuardado) {
            actualizarLongitudTelefono();
            return;
        }

        const valor = valorGuardado.trim();
        const prefijos = Array.from(selectPrefijo.options)
            .map(function (opcion) { return opcion.value; })
            .sort(function (a, b) { return b.length - a.length; });

        const prefijoEncontrado = prefijos.find(function (prefijo) {
            return valor.startsWith(prefijo);
        });

        if (prefijoEncontrado) {
            selectPrefijo.value = prefijoEncontrado;
            inputNumero.value = valor.slice(prefijoEncontrado.length).replace(/\D/g, '');
        } else {
            inputNumero.value = valor.replace(/\D/g, '') || valor;
        }
        actualizarLongitudTelefono();
    }

    if (selectPrefijo && inputNumero) {
        selectPrefijo.addEventListener('change', actualizarLongitudTelefono);
        inputNumero.addEventListener('input', function () {
            inputNumero.value = inputNumero.value.replace(/\D/g, '');
        });
        actualizarLongitudTelefono();
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
        formulario.dataset.redirigirA = '/clientes';
        titulo.textContent = 'Nuevo cliente';
        cargarTelefono('');
        modal.showModal();
    }

    function abrirParaEditar(boton) {
        formulario.reset();
        ocultarError();
        formulario.action = `/clientes/${boton.dataset.id}/editar`;
        formulario.dataset.redirigirA = boton.dataset.redirigirA || '/clientes';
        formulario.elements['nombre'].value = boton.dataset.nombre || '';
        formulario.elements['email'].value = boton.dataset.email || '';
        cargarTelefono(boton.dataset.telefono || '');
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
        combinarTelefono();

        if (inputNumero && inputNumero.value) {
            const opcion = selectPrefijo.options[selectPrefijo.selectedIndex];
            const longitudEsperada = opcion ? Number(opcion.dataset.longitud) : null;
            if (longitudEsperada && inputNumero.value.length !== longitudEsperada) {
                mostrarError(`El teléfono para ${opcion.text} debe tener ${longitudEsperada} números (sin contar el prefijo).`);
                return;
            }
        }

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
                    window.location.href = formulario.dataset.redirigirA || '/clientes';
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
        formulario.dataset.redirigirA = '/proyectos';
        titulo.textContent = 'Nuevo proyecto';
        // No dejamos elegir una fecha de entrega que ya pasó para un proyecto
        // nuevo. Al editar uno existente no se restringe, para no bloquear
        // guardar otros cambios en un proyecto que ya quedó vencido.
        formulario.elements['fecha_entrega'].min = new Date().toISOString().slice(0, 10);
        modal.showModal();
    }

    function abrirParaEditar(boton) {
        formulario.reset();
        ocultarError();
        formulario.action = `/proyectos/${boton.dataset.id}/editar`;
        formulario.dataset.redirigirA = boton.dataset.redirigirA || '/proyectos';
        formulario.elements['titulo'].value = boton.dataset.titulo || '';
        formulario.elements['cliente_id'].value = boton.dataset.clienteId || '';
        formulario.elements['estado'].value = boton.dataset.estado || '';
        // Si el proyecto ya tenía una fecha vencida, la dejamos como mínimo
        // para no bloquear guardar otros cambios sin tocar la fecha — pero
        // no se puede elegir una fecha pasada nueva distinta a esa.
        const fechaExistente = boton.dataset.fechaEntrega || '';
        const hoy = new Date().toISOString().slice(0, 10);
        formulario.elements['fecha_entrega'].min = fechaExistente && fechaExistente < hoy ? fechaExistente : hoy;
        formulario.elements['fecha_entrega'].value = fechaExistente;
        formulario.elements['presupuesto'].value = boton.dataset.presupuesto || '';
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
                    window.location.href = formulario.dataset.redirigirA || '/proyectos';
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

function inicializarModalPago() {
    const modal = document.getElementById('modal-pago');
    const formulario = document.getElementById('formulario-pago');
    const titulo = document.getElementById('modal-pago-titulo');
    const contenedorError = document.getElementById('modal-pago-error');

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
            boton.value = 'Guardar';
        }
    }

    function abrirParaNuevo() {
        formulario.reset();
        ocultarError();
        formulario.action = '/pagos/nuevo';
        formulario.dataset.redirigirA = '/pagos';
        titulo.textContent = 'Nuevo pago';
        modal.showModal();
    }

    function abrirParaEditar(boton) {
        formulario.reset();
        ocultarError();
        formulario.action = `/pagos/${boton.dataset.id}/editar`;
        formulario.dataset.redirigirA = boton.dataset.redirigirA || '/pagos';
        formulario.elements['proyecto_id'].value = boton.dataset.proyectoId || '';
        formulario.elements['monto'].value = boton.dataset.monto || '';
        formulario.elements['fecha'].value = boton.dataset.fecha || '';
        formulario.elements['estado'].value = boton.dataset.estado || 'cobrado';
        titulo.textContent = 'Editar pago';
        modal.showModal();
    }

    document.querySelectorAll('.boton-nuevo-pago').forEach(function (boton) {
        boton.addEventListener('click', abrirParaNuevo);
    });

    document.querySelectorAll('.boton-editar-pago').forEach(function (boton) {
        boton.addEventListener('click', function () {
            abrirParaEditar(boton);
        });
    });

    const botonCancelar = document.getElementById('boton-cancelar-modal-pago');
    const botonCerrar = document.getElementById('boton-cerrar-modal-pago');
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
                    window.location.href = formulario.dataset.redirigirA || '/pagos';
                } else {
                    mostrarError(datos.error || 'Ocurrió un error al guardar el pago.');
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
        const botonPago = document.querySelector(`.boton-editar-pago[data-id="${parametros.get('editar')}"]`);
        if (botonPago) {
            abrirParaEditar(botonPago);
        }
    }

    if (parametros.has('nuevo') || parametros.has('editar')) {
        const url = new URL(window.location);
        url.searchParams.delete('nuevo');
        url.searchParams.delete('editar');
        window.history.replaceState({}, '', url);
    }
}

function inicializarModalNota() {
    const modal = document.getElementById('modal-nota');
    const formulario = document.getElementById('formulario-nota');
    const titulo = document.getElementById('modal-nota-titulo');
    const contenedorError = document.getElementById('modal-nota-error');
    const seccionIa = document.getElementById('seccion-ia-nota');

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
            boton.value = 'Guardar';
        }
    }

    function abrirParaNuevo() {
        formulario.reset();
        ocultarError();
        formulario.action = '/notas/nuevo';
        formulario.dataset.redirigirA = '/notas';
        titulo.textContent = 'Nueva nota';
        if (seccionIa) {
            seccionIa.hidden = false;
        }
        modal.showModal();
    }

    function abrirParaEditar(boton) {
        formulario.reset();
        ocultarError();
        formulario.action = `/notas/${boton.dataset.id}/editar`;
        formulario.dataset.redirigirA = boton.dataset.redirigirA || '/notas';
        formulario.elements['cliente_id'].value = boton.dataset.clienteId || '';
        formulario.elements['contenido'].value = boton.dataset.contenido || '';
        formulario.elements['fecha'].value = boton.dataset.fecha || '';
        titulo.textContent = 'Editar nota';
        if (seccionIa) {
            seccionIa.hidden = true;
        }
        modal.showModal();
    }

    document.querySelectorAll('.boton-nueva-nota').forEach(function (boton) {
        boton.addEventListener('click', abrirParaNuevo);
    });

    document.querySelectorAll('.boton-editar-nota').forEach(function (boton) {
        boton.addEventListener('click', function () {
            abrirParaEditar(boton);
        });
    });

    const botonCancelar = document.getElementById('boton-cancelar-modal-nota');
    const botonCerrar = document.getElementById('boton-cerrar-modal-nota');
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

    const botonGenerarIa = document.getElementById('boton-generar-ia-nota');
    if (botonGenerarIa) {
        botonGenerarIa.addEventListener('click', function () {
            const clienteId = formulario.elements['cliente_id'].value;
            const palabrasClave = document.getElementById('modal-palabras-clave').value;

            botonGenerarIa.disabled = true;
            botonGenerarIa.textContent = botonGenerarIa.dataset.cargando;

            const datosFormulario = new FormData();
            datosFormulario.set('cliente_id', clienteId);
            datosFormulario.set('palabras_clave', palabrasClave);
            datosFormulario.set('csrf_token', formulario.elements['csrf_token'].value);

            fetch('/notas/generar-ia', {
                method: 'POST',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
                body: datosFormulario
            })
                .then(function (respuesta) {
                    return respuesta.json();
                })
                .then(function (datos) {
                    if (datos.exito) {
                        formulario.elements['contenido'].value = datos.borrador;
                    } else {
                        mostrarError(datos.error || 'No se pudo generar el borrador.');
                    }
                })
                .catch(function () {
                    mostrarError('No se pudo conectar con el servidor. Probá de nuevo.');
                })
                .finally(function () {
                    botonGenerarIa.disabled = false;
                    botonGenerarIa.innerHTML = botonGenerarIa.dataset.textoOriginal;
                });
        });
        botonGenerarIa.dataset.textoOriginal = botonGenerarIa.innerHTML;
    }

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
                    window.location.href = formulario.dataset.redirigirA || '/notas';
                } else {
                    mostrarError(datos.error || 'Ocurrió un error al guardar la nota.');
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
        const botonNota = document.querySelector(`.boton-editar-nota[data-id="${parametros.get('editar')}"]`);
        if (botonNota) {
            abrirParaEditar(botonNota);
        }
    }

    if (parametros.has('nuevo') || parametros.has('editar')) {
        const url = new URL(window.location);
        url.searchParams.delete('nuevo');
        url.searchParams.delete('editar');
        window.history.replaceState({}, '', url);
    }
}

function inicializarModalUsuario() {
    const modal = document.getElementById('modal-usuario');
    const formulario = document.getElementById('formulario-usuario');
    const contenedorError = document.getElementById('modal-usuario-error');
    const botonAbrir = document.getElementById('boton-nuevo-usuario');

    if (!modal || !formulario || !botonAbrir) {
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
            boton.value = 'Agregar usuario';
        }
    }

    botonAbrir.addEventListener('click', function () {
        formulario.reset();
        ocultarError();
        modal.showModal();
    });

    const botonCancelar = document.getElementById('boton-cancelar-modal-usuario');
    const botonCerrar = document.getElementById('boton-cerrar-modal-usuario');
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
                    window.location.href = '/usuarios';
                } else {
                    mostrarError(datos.error || 'Ocurrió un error al guardar el usuario.');
                }
            })
            .catch(function () {
                mostrarError('No se pudo conectar con el servidor. Probá de nuevo.');
            });
    });
}

function inicializarConfirmacionEliminar() {
    const modal = document.getElementById('modal-confirmar-eliminar');
    const mensaje = document.getElementById('modal-confirmar-eliminar-mensaje');
    const botonConfirmar = document.getElementById('boton-confirmar-eliminar');
    const botonCancelar = document.getElementById('boton-cancelar-eliminar');

    if (!modal) {
        return;
    }

    let formularioPendiente = null;

    document.querySelectorAll('.form-eliminar').forEach(function (formulario) {
        formulario.addEventListener('submit', function (evento) {
            evento.preventDefault();
            formularioPendiente = formulario;
            mensaje.textContent = formulario.dataset.mensaje || 'Esta acción no se puede deshacer.';
            modal.showModal();
        });
    });

    botonConfirmar.addEventListener('click', function () {
        if (formularioPendiente) {
            formularioPendiente.submit();
        }
        modal.close();
    });

    botonCancelar.addEventListener('click', function () {
        modal.close();
        formularioPendiente = null;
    });

    modal.addEventListener('click', function (evento) {
        if (evento.target === modal) {
            modal.close();
        }
    });
}

function inicializarTogglesPassword() {
    // Busca el input de contraseña como hermano inmediatamente anterior al
    // botón, en vez de depender de un id fijo: así funciona en cualquier
    // formulario (login, alta de usuario, etc.) sin importar cuántos haya
    // en la página, y no se rompe si el id del campo cambia.
    document.querySelectorAll('.boton-ver-password').forEach(function (boton) {
        const campo = boton.previousElementSibling;
        if (!campo || campo.tagName !== 'INPUT') {
            return;
        }
        boton.addEventListener('click', function () {
            const mostrando = campo.type === 'text';
            campo.type = mostrando ? 'password' : 'text';
            boton.classList.toggle('activo', !mostrando);
            boton.setAttribute('aria-pressed', String(!mostrando));
            boton.setAttribute('aria-label', mostrando ? 'Mostrar contraseña' : 'Ocultar contraseña');
        });
    });
}

function inicializarZonaArchivo() {
    const zona = document.getElementById('zona-archivo');
    const input = document.getElementById('archivo_csv');
    const nombreMostrado = document.getElementById('zona-archivo-nombre');

    if (!zona || !input) {
        return;
    }

    function mostrarNombre(nombre) {
        if (!nombreMostrado) {
            return;
        }
        nombreMostrado.textContent = nombre;
        nombreMostrado.hidden = !nombre;
    }

    input.addEventListener('change', function () {
        const archivo = input.files && input.files[0];
        mostrarNombre(archivo ? archivo.name : '');
    });

    ['dragover', 'dragenter'].forEach(function (evento) {
        zona.addEventListener(evento, function (e) {
            e.preventDefault();
            zona.classList.add('arrastrando');
        });
    });

    ['dragleave', 'dragend'].forEach(function (evento) {
        zona.addEventListener(evento, function () {
            zona.classList.remove('arrastrando');
        });
    });

    zona.addEventListener('drop', function (e) {
        e.preventDefault();
        zona.classList.remove('arrastrando');
        const archivos = e.dataTransfer.files;
        if (archivos && archivos.length) {
            input.files = archivos;
            mostrarNombre(archivos[0].name);
        }
    });
}

function inicializarFotoPerfil() {
    const input = document.getElementById('foto_perfil');
    if (!input) {
        return;
    }

    input.addEventListener('change', function () {
        const archivo = input.files && input.files[0];
        if (!archivo) {
            return;
        }

        const url = URL.createObjectURL(archivo);
        const actual = document.getElementById('foto-perfil-preview');
        if (actual && actual.tagName === 'IMG') {
            actual.src = url;
        } else if (actual) {
            const nuevaImagen = document.createElement('img');
            nuevaImagen.id = 'foto-perfil-preview';
            nuevaImagen.className = 'foto-perfil-preview';
            nuevaImagen.alt = '';
            nuevaImagen.src = url;
            actual.replaceWith(nuevaImagen);
        }
    });
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
document.addEventListener('DOMContentLoaded', inicializarMenusDesplegables);
document.addEventListener('DOMContentLoaded', inicializarBuscadores);
document.addEventListener('DOMContentLoaded', inicializarZonaArchivo);
document.addEventListener('DOMContentLoaded', inicializarFotoPerfil);
document.addEventListener('DOMContentLoaded', inicializarModalCliente);
document.addEventListener('DOMContentLoaded', inicializarModalProyecto);
document.addEventListener('DOMContentLoaded', inicializarModalPago);
document.addEventListener('DOMContentLoaded', inicializarModalNota);
document.addEventListener('DOMContentLoaded', inicializarModalUsuario);
document.addEventListener('DOMContentLoaded', inicializarTogglesPassword);
document.addEventListener('DOMContentLoaded', inicializarConfirmacionEliminar);