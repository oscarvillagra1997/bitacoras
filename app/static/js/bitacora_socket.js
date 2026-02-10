// Este archivo asume que bitacora_core.js YA fue cargado
// y que existen: currentClienteId, aplicarSnapshotInicial, agregarFilaEvento,
// aplicarUpdateEventoRemoto, eliminarFilaEventoRemoto, aplicarFormUpdateRemoto, emitirFormUpdate.

function inicializarSocket() {
    try {
        window.socket = io({
            query: {
                cliente_id: currentClienteId || ""
            }
        });

        window.socket.on("connect", () => {
            console.log("✅ Conectado a Socket.IO");
            const estado = document.getElementById("estado-socket");
            if (estado) estado.textContent = "Conectado";
        });

        window.socket.on("disconnect", () => {
            console.log("⚠️ Desconectado de Socket.IO");
            const estado = document.getElementById("estado-socket");
            if (estado) estado.textContent = "Desconectado";
        });

        window.socket.on("user_count", (data) => {
            const span = document.getElementById("usuarios-conectados");
            if (span && data && typeof data.conectados === "number") {
                span.textContent = data.conectados;
            }
        });

        // Snapshot inicial
        window.socket.on("snapshot_inicial", (data) => {
            console.log("📦 Snapshot recibido:", data);
            aplicarSnapshotInicial(data);
        });

        // otro usuario creó una fila nueva
        window.socket.on("evento_nuevo", (data) => {
            console.log("📢 evento_nuevo desde otro cliente:", data);
            // data.row debería traer toda la info
            agregarFilaEvento(false, data.row || { id: data.id });
        });

        // otro usuario modificó un campo
        window.socket.on("evento_update", (data) => {
            aplicarUpdateEventoRemoto(data);
        });

        // otro usuario eliminó una fila
        window.socket.on("evento_eliminar", (data) => {
            eliminarFilaEventoRemoto(data);
        });

        // actualización de operadores / horario / fechas
        window.socket.on("form_update", (data) => {
            aplicarFormUpdateRemoto(data);
        });

        // ping de prueba
        window.socket.emit("bitacora_ping", {
            mensaje: "Hola, acabo de abrir la pantalla de bitácora",
            timestamp: new Date().toISOString(),
        });

    } catch (err) {
        console.error("Error inicializando Socket.IO:", err);
        const estado = document.getElementById("estado-socket");
        if (estado) estado.textContent = "Error al conectar";
    }
}

// cuando el DOM está listo, inicializamos el socket
document.addEventListener('DOMContentLoaded', () => {
    inicializarSocket();
});
