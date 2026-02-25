// static/js/bitacora_socket.js

function inicializarSocket() {
  try {
    // ✅ Evita doble conexión
    if (window.socket && window.socket.connected) return;

    const base = (window.APP_BASE || "").replace(/\/+$/, "");
    const socketPath = base ? `${base}/socket.io` : "/socket.io";

    window.socket = io({
      path: socketPath,
      query: { cliente_id: currentClienteId || "" }
    });

    const estado = document.getElementById("estado-socket");

    window.socket.on("connect", () => {
      if (estado) estado.textContent = "Conectado";
    });

    window.socket.on("disconnect", () => {
      if (estado) estado.textContent = "Desconectado";
    });

    window.socket.on("user_count", (data) => {
      const span = document.getElementById("usuarios-conectados");
      if (span && data && typeof data.conectados === "number") {
        span.textContent = data.conectados;
      }
    });

    window.socket.on("snapshot_inicial", (data) => {
      aplicarSnapshotInicial(data);
    });

    window.socket.on("evento_nuevo", (data) => {
      // El servidor en tu sockets.py emite row_data, no {row:...}
      agregarFilaEvento(false, data);
    });

    window.socket.on("evento_update", (data) => {
      aplicarUpdateEventoRemoto(data);
    });

    window.socket.on("evento_eliminar", (data) => {
      eliminarFilaEventoRemoto(data);
    });

    window.socket.on("form_update", (data) => {
      SUPRIMIR_EMIT_FORM = true;
      aplicarFormUpdateRemoto(data);
      SUPRIMIR_EMIT_FORM = false;
    });

    window.socket.on("bitacora_vaciada", (data) => {
      vaciarBitacoraUI({ mantenerCliente: true });

      Swal.fire({
        icon: "success",
        title: "Bitácora vaciada",
        timer: 1200,
        showConfirmButton: false
      });
    });

  } catch (err) {
    console.error("Error inicializando Socket.IO:", err);
    const estado = document.getElementById("estado-socket");
    if (estado) estado.textContent = "Error al conectar";
  }
}

// Para que el core pueda reconectar al cambiar cliente
window.inicializarSocket = inicializarSocket;

window.reconectarSocketCliente = function(clienteId) {
  currentClienteId = clienteId || null;

  if (window.socket) {
    try { window.socket.disconnect(); } catch (_) {}
    window.socket = null;
  }
  inicializarSocket();
};

document.addEventListener("DOMContentLoaded", () => {
  inicializarSocket();
});