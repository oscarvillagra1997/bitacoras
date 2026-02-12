// ==========================
// VARIABLES GLOBALES (sin socket)
// ==========================
window.socket = window.socket || null;   // 👈 socket vive en window, lo rellenará el otro archivo

let operadoresContainer = null;
let eventosContainer    = null;
let operadorTemplate    = null;
let eventoTemplate      = null;
let btnAgregarOperador  = null;
let btnAgregarEvento    = null;
let clienteSelect       = null;

let lugaresDisponibles  = []; // [{id, nombre}, ...]
let currentClienteId    = null;


// ==========================
// UTIL: UUID simple
// ==========================
function crearUUID() {
    return "row-" + Math.random().toString(36).substring(2, 10) + Date.now();
}


// ==========================
// SNAPSHOT INICIAL
// ==========================
function aplicarSnapshotInicial(data) {
    if (!data) return;

    // 1) Formulario general
    aplicarFormUpdateRemoto(data.form || {});

    // 2) Eventos
    if (!eventosContainer || !eventoTemplate) return;

    eventosContainer.innerHTML = ""; // limpiamos todo

    const eventos = data.eventos || [];
    eventos.forEach(ev => {
        agregarFilaEvento(false, ev);
    });
}


// ==========================
// FORM GENERAL (operadores / horario / fechas)
// ==========================
function emitirFormUpdate() {
    if (!window.socket) return;

    const operadoresSelects = operadoresContainer
        ? operadoresContainer.querySelectorAll('select[name="operadores[]"]')
        : [];

    const operadoresIds = Array.from(operadoresSelects).map(s => s.value).filter(v => v);

    const horarioSelect = document.querySelector('select[name="horario"]');
    const fechaInicio   = document.querySelector('input[name="fecha_inicio"]');
    const fechaFin      = document.querySelector('input[name="fecha_fin"]');

    const payload = {
        operadores:   operadoresIds,
        horario:      horarioSelect ? horarioSelect.value : "",
        fecha_inicio: fechaInicio   ? fechaInicio.value   : "",
        fecha_fin:    fechaFin      ? fechaFin.value      : ""
    };

    window.socket.emit("form_update", payload);
}

function aplicarFormUpdateRemoto(data) {
    if (!data) return;

    // ========= OPERADORES =========
    if (operadoresContainer && operadorTemplate) {
        const opIds = data.operadores || [];

        // Cuántos selects hay actualmente
        let selects = operadoresContainer.querySelectorAll('select[name="operadores[]"]');
        const actuales = selects.length;
        const necesarios = opIds.length;

        // 1) Crear filas adicionales si faltan
        if (necesarios > actuales) {
            const diff = necesarios - actuales;
            for (let i = 0; i < diff; i++) {
                const clone = operadorTemplate.content.cloneNode(true);
                operadoresContainer.appendChild(clone);
            }
        }

        // 2) Eliminar filas sobrantes si hay más que las necesarias
        if (necesarios < actuales) {
            const diff = actuales - necesarios;
            for (let i = 0; i < diff; i++) {
                // elimino desde el final
                const lastGroup = operadoresContainer.querySelector('.input-group:last-of-type');
                if (lastGroup) lastGroup.remove();
            }
        }

        // 3) Vuelvo a pedir los selects (porque pueden haber cambiado)
        selects = operadoresContainer.querySelectorAll('select[name="operadores[]"]');

        // 4) Asignar los valores recibidos
        selects.forEach((sel, idx) => {
            sel.value = opIds[idx] || "";
        });
    }

    // ========= HORARIO =========
    const horarioSelect = document.querySelector('select[name="horario"]');
    if (horarioSelect && data.horario !== undefined) {
        horarioSelect.value = data.horario;
    }

    // ========= FECHAS =========
    const fechaInicio = document.querySelector('input[name="fecha_inicio"]');
    if (fechaInicio && data.fecha_inicio !== undefined) {
        fechaInicio.value = data.fecha_inicio;
    }

    const fechaFin = document.querySelector('input[name="fecha_fin"]');
    if (fechaFin && data.fecha_fin !== undefined) {
        fechaFin.value = data.fecha_fin;
    }
}



// ==========================
// LUGARES
// ==========================
function poblarSelectLugares(select) {
    select.innerHTML = '<option value="">Seleccionar Lugar</option>';

    lugaresDisponibles.forEach(lugar => {
        const opt = document.createElement('option');
        opt.value = lugar.id;
        opt.textContent = lugar.nombre;
        select.appendChild(opt);
    });
}

function resetLugaresEnEventos() {
    const selectsLugares = document.querySelectorAll('select[name="lugares[]"]');
    selectsLugares.forEach(sel => {
        sel.innerHTML = '<option value="">Seleccione un cliente...</option>';
    });
}

function actualizarTodosLosSelectsLugares() {
    const selectsLugares = document.querySelectorAll('select[name="lugares[]"]');
    selectsLugares.forEach(sel => poblarSelectLugares(sel));
}


// ==========================
// FILAS DE EVENTO
// ==========================
function agregarFilaEvento(emitirPorSocket = true, rowData = null) {
    if (!eventoTemplate || !eventosContainer) return;

    const clone = eventoTemplate.content.cloneNode(true);
    const group = clone.querySelector('.input-group');
    if (!group) return;

    const rowId = rowData && rowData.id ? rowData.id : crearUUID();
    group.dataset.rowId = rowId;

    const selectLugar = group.querySelector('select[name="lugares[]"]');
    const inputCamara = group.querySelector('input[name="camaras[]"]');
    const inputHora   = group.querySelector('input[name="horas_evento[]"]');
    const selectTipo  = group.querySelector('select[name="tipos_evento[]"]');
    const inputObs    = group.querySelector('input[name="observaciones[]"]');

    // poblar lugares
    if (selectLugar) {
        if (lugaresDisponibles.length > 0) {
            poblarSelectLugares(selectLugar);
        } else {
            selectLugar.innerHTML = '<option value="">Seleccione un cliente...</option>';
        }
    }

    // Si viene data desde el servidor → aplicar valores
    if (rowData) {
        if (selectLugar && rowData.lugar_id != null) {
            selectLugar.value = String(rowData.lugar_id);
        }
        if (inputCamara && rowData.camara != null) {
            inputCamara.value = rowData.camara;
        }
        if (inputHora && rowData.hora != null) {
            inputHora.value = rowData.hora;
        }
        if (selectTipo && rowData.tipo_evento_id != null) {
            selectTipo.value = String(rowData.tipo_evento_id);
        }
        if (inputObs && rowData.observaciones != null) {
            inputObs.value = rowData.observaciones;
        }
    }

    eventosContainer.appendChild(clone);

    // Si la fila la creó este usuario → avisar al servidor
    if (emitirPorSocket && window.socket) {
        window.socket.emit("evento_nuevo", {
            id: rowId,
            row: {
                id:             rowId,
                lugar_id:       selectLugar ? selectLugar.value || null : null,
                camara:         inputCamara ? inputCamara.value : "",
                hora:           inputHora   ? inputHora.value   : "",
                tipo_evento_id: selectTipo  ? selectTipo.value  || null : null,
                observaciones:  inputObs    ? inputObs.value    : ""
            }
        });
    }
}

// cambio remoto de una celda
function aplicarUpdateEventoRemoto(data) {
    if (!data || !eventosContainer) return;

    const rowId = data.id;
    const field = data.field;
    const value = data.value;

    if (!rowId || !field) return;

    const row = eventosContainer.querySelector(`.input-group[data-row-id="${rowId}"]`);
    if (!row) return;

    let elem = null;
    switch (field) {
        case "lugar_id":
            elem = row.querySelector('select[name="lugares[]"]');
            break;
        case "camara":
            elem = row.querySelector('input[name="camaras[]"]');
            break;
        case "hora":
            elem = row.querySelector('input[name="horas_evento[]"]');
            break;
        case "tipo_evento_id":
            elem = row.querySelector('select[name="tipos_evento[]"]');
            break;
        case "observaciones":
            elem = row.querySelector('input[name="observaciones[]"]');
            break;
    }

    if (elem) elem.value = value != null ? value : "";
}


// eliminación remota
function eliminarFilaEventoRemoto(data) {
    if (!data || !eventosContainer) return;
    const rowId = data.id;
    if (!rowId) return;

    const row = eventosContainer.querySelector(`.input-group[data-row-id="${rowId}"]`);
    if (row) row.remove();
}


// ==========================
// DOM READY
// ==========================
document.addEventListener('DOMContentLoaded', () => {

    operadoresContainer = document.getElementById('operadores-container');
    eventosContainer    = document.getElementById('eventos-container');

    operadorTemplate    = document.getElementById('operador-row-template');
    eventoTemplate      = document.getElementById('evento-row-template');

    btnAgregarOperador  = document.getElementById('agregar-operador');
    btnAgregarEvento    = document.getElementById('agregar-evento');

    clienteSelect       = document.getElementById('cliente');

    currentClienteId = clienteSelect ? clienteSelect.value || null : null;

    // ====== CAMBIO DE CLIENTE → LUGARES ======
    if (clienteSelect) {
        clienteSelect.addEventListener('change', async (e) => {
            const clienteId = e.target.value;
            currentClienteId = clienteId || null;

            resetLugaresEnEventos();
            lugaresDisponibles = [];

            if (!clienteId) return;

            try {
                const resp = await fetch(`${window.APP_BASE}/api/lugares/${clienteId}`);
                if (!resp.ok) throw new Error("Error al cargar lugares");

                const data = await resp.json();
                lugaresDisponibles = Array.isArray(data) ? data : (data.lugares || []);
                actualizarTodosLosSelectsLugares();
            } catch (err) {
                console.error("Error obteniendo lugares:", err);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudieron cargar los lugares para este cliente.'
                });
            }
        });
    }

    // ====== OPERADORES: agregar / eliminar ======
    if (btnAgregarOperador && operadorTemplate && operadoresContainer) {
        btnAgregarOperador.addEventListener('click', () => {
            const clone = operadorTemplate.content.cloneNode(true);
            operadoresContainer.appendChild(clone);
            emitirFormUpdate();
        });
    }

    if (operadoresContainer) {
        operadoresContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-operador')) {
                const group = e.target.closest('.input-group');
                if (group) group.remove();
                emitirFormUpdate();
            }
        });

        operadoresContainer.addEventListener('change', () => {
            emitirFormUpdate();
        });
    }

    // Horario / fechas
    const horarioSelect = document.querySelector('select[name="horario"]');
    const fechaInicio   = document.querySelector('input[name="fecha_inicio"]');
    const fechaFin      = document.querySelector('input[name="fecha_fin"]');

    horarioSelect?.addEventListener('change', emitirFormUpdate);
    fechaInicio?.addEventListener('change', emitirFormUpdate);
    fechaFin?.addEventListener('change', emitirFormUpdate);

    // ====== EVENTOS: agregar ======
    if (btnAgregarEvento && eventoTemplate && eventosContainer) {
        btnAgregarEvento.addEventListener('click', () => {
            agregarFilaEvento(true);
        });
    }

    // ====== EVENTOS: eliminar + cambios de celdas ======
    if (eventosContainer) {
        eventosContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-evento')) {
                const group = e.target.closest('.input-group');
                if (!group) return;

                const rowId = group.dataset.rowId;
                group.remove();

                if (window.socket && rowId) {
                    window.socket.emit("evento_eliminar", { id: rowId });
                }
            }
        });

        eventosContainer.addEventListener('change', (e) => {
            const group = e.target.closest('.input-group');
            if (!group || !window.socket) return;

            const rowId = group.dataset.rowId;
            if (!rowId) return;

            let field = null;
            let value = e.target.value;

            if (e.target.name === "lugares[]") {
                field = "lugar_id";
            } else if (e.target.name === "camaras[]") {
                field = "camara";
            } else if (e.target.name === "horas_evento[]") {
                field = "hora";
            } else if (e.target.name === "tipos_evento[]") {
                field = "tipo_evento_id";
            } else if (e.target.name === "observaciones[]") {
                field = "observaciones";
            }

            if (!field) return;

            window.socket.emit("evento_update", {
                id: rowId,
                field: field,
                value: value
            });
        });
    }

    // Si ya hay cliente seleccionado al cargar, disparar carga de lugares
    if (clienteSelect && clienteSelect.value) {
        const event = new Event('change');
        clienteSelect.dispatchEvent(event);
    }
});


// ==========================
// EXPORTAR XLSX ANTES DE ENVIAR
// ==========================
window.exportarXLSXAntesDeEnviar = function (form) {
    const operadores = Array.from(form.querySelectorAll('[name="operadores[]"]')).map(e => {
        const selected = e.options[e.selectedIndex];
        return selected ? selected.text : '';
    }).join(', ');

    const horario      = form.horario.value;
    const fecha_inicio = form.fecha_inicio.value;
    const fecha_fin    = form.fecha_fin.value;

    const clienteSelect = form.querySelector('select[name="cliente_id"]');
    const clienteTexto  = clienteSelect && clienteSelect.options[clienteSelect.selectedIndex]
        ? clienteSelect.options[clienteSelect.selectedIndex].text
        : '';

    const eventos = Array.from(form.querySelectorAll('#eventos-container .input-group')).map(group => {
        const selects = group.querySelectorAll('select');
        const inputs  = group.querySelectorAll('input');

        return {
            'Lugar':          selects[0]?.selectedOptions[0]?.text || '',
            'Cámara':         inputs[0]?.value || '',
            'Hora Evento':    inputs[1]?.value || '',
            'Tipo de Evento': selects[1]?.selectedOptions[0]?.text || '',
            'Observaciones':  inputs[2]?.value || ''
        };
    }).filter(ev => ev['Lugar'] && ev['Hora Evento']);

    const ws_eventos = XLSX.utils.json_to_sheet(eventos);

    const metadata = [
        { 'Campo': 'Cliente',      'Valor': clienteTexto },
        { 'Campo': 'Operadores',   'Valor': operadores },
        { 'Campo': 'Horario',      'Valor': horario },
        { 'Campo': 'Fecha Inicio', 'Valor': fecha_inicio },
        { 'Campo': 'Fecha Fin',    'Valor': fecha_fin }
    ];
    const ws_metadata = XLSX.utils.json_to_sheet(metadata);

    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws_metadata, 'Resumen');
    XLSX.utils.book_append_sheet(wb, ws_eventos,  'Eventos');

    const hoy = new Date().toISOString().split('T')[0];
    XLSX.writeFile(wb, `bitacora_${hoy}.xlsx`);
};


// ==========================
// CONFIRMAR ENVÍO
// ==========================
window.confirmarEnvio = function (event) {
    event.preventDefault();

    const form = event.target.closest("form");
    let error = false;

    const clienteSelect = form.querySelector('select[name="cliente_id"]');
    if (clienteSelect && !clienteSelect.value) {
        clienteSelect.classList.add('is-invalid');
        error = true;
    } else if (clienteSelect) {
        clienteSelect.classList.remove('is-invalid');
    }

    const tipoEventoSelects = form.querySelectorAll('select[name="tipos_evento[]"]');
    tipoEventoSelects.forEach(select => {
        if (!select.value) {
            select.classList.add('is-invalid');
            error = true;
        } else {
            select.classList.remove('is-invalid');
        }
    });

    const horaInputs = form.querySelectorAll('input[name="horas_evento[]"]');
    horaInputs.forEach(input => {
        if (!input.value) {
            input.classList.add('is-invalid');
            error = true;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    const camaraInputs = form.querySelectorAll('input[name="camaras[]"]');
    camaraInputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            error = true;
        } else {
            input.classList.remove('is-invalid');
        }
    });

    const operadorSelects = form.querySelectorAll('select[name="operadores[]"]');
    operadorSelects.forEach(select => {
        if (!select.value) {
            select.classList.add('is-invalid');
            error = true;
        } else {
            select.classList.remove('is-invalid');
        }
    });

    const horarioSelect = form.querySelector('select[name="horario"]');
    if (!horarioSelect.value) {
        horarioSelect.classList.add('is-invalid');
        error = true;
    } else {
        horarioSelect.classList.remove('is-invalid');
    }

    const fechaInicio = form.querySelector('input[name="fecha_inicio"]');
    const fechaFin    = form.querySelector('input[name="fecha_fin"]');

    if (!fechaInicio.value) {
        fechaInicio.classList.add('is-invalid');
        error = true;
    } else {
        fechaInicio.classList.remove('is-invalid');
    }

    if (!fechaFin.value) {
        fechaFin.classList.add('is-invalid');
        error = true;
    } else {
        fechaFin.classList.remove('is-invalid');
    }

    if (fechaInicio.value && fechaFin.value && fechaFin.value < fechaInicio.value) {
        fechaFin.classList.add('is-invalid');
        fechaInicio.classList.add('is-invalid');
        Swal.fire({
            icon: 'error',
            title: 'Fechas inválidas',
            text: 'La fecha de finalización no puede ser anterior a la fecha de inicio.',
        });
        return;
    }

    if (error) {
        Swal.fire({
            icon: 'error',
            title: 'Campos incompletos',
            text: 'Por favor, completa correctamente todos los campos requeridos antes de continuar.',
        });
        return;
    }

    Swal.fire({
        title: "¿Está seguro?",
        text: "Una vez enviada, no se podrá modificar.",
        icon: "warning",
        showCancelButton: true,
        confirmButtonColor: "#d33",
        cancelButtonColor: "#3085d6",
        confirmButtonText: "Sí, crear bitácora",
        cancelButtonText: "Cancelar"
    }).then((result) => {
        if (result.isConfirmed) {
            exportarXLSXAntesDeEnviar(form);
            setTimeout(() => {
                form.noValidate = true;
                form.submit();
            }, 500);
        }
    });
};


// ==========================
// IMPORTAR EVENTOS DESDE EXCEL
// ==========================
document.getElementById("excel-input")?.addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();

    reader.onload = function (event) {
        const data     = new Uint8Array(event.target.result);
        const workbook = XLSX.read(data, { type: "array" });

        const sheetName = workbook.SheetNames.find(n => n.toLowerCase() === "eventos");
        if (!sheetName) {
            alert("La hoja 'Eventos' no existe en el archivo Excel.");
            return;
        }

        const sheet   = workbook.Sheets[sheetName];
        const eventos = XLSX.utils.sheet_to_json(sheet);

        const eventosContainer = document.getElementById("eventos-container");
        const eventoTemplate   = document.getElementById("evento-row-template");

        eventosContainer.innerHTML = "";

        eventos.forEach(ev => {
            const clone   = eventoTemplate.content.cloneNode(true);
            const group   = clone.querySelector('.input-group');
            const selects = clone.querySelectorAll("select");
            const inputs  = clone.querySelectorAll("input");

            const lugar  = ev["Lugar"] || "";
            const camara = ev["Cámara"] || "";
            const hora   = ev["Hora Evento"] || "";
            const tipo   = ev["Tipo de Evento"] || "";
            const obs    = ev["Observaciones"] || "";

            group.dataset.rowId = crearUUID();

            selects[0].value = encontrarOpcionPorTexto(selects[0], lugar);
            inputs[0].value  = camara;
            inputs[1].value  = hora;
            selects[1].value = encontrarOpcionPorTexto(selects[1], tipo);
            inputs[2].value  = obs;

            eventosContainer.appendChild(clone);
        });

        Swal.fire({
            icon: "success",
            title: "Eventos cargados",
            text: `${eventos.length} eventos importados desde Excel.`,
            timer: 2000,
            showConfirmButton: false
        });
    };

    reader.readAsArrayBuffer(file);
});


// ==========================
// 🔍 Función auxiliar para buscar una opción por texto visible
// ==========================
function encontrarOpcionPorTexto(select, texto) {
    texto = (texto || '').trim().toLowerCase();

    for (let option of select.options) {
        if (option.text.trim().toLowerCase() === texto) {
            return option.value;
        }
    }
    return "";
}
