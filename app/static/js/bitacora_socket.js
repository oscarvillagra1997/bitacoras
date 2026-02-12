// bitacora_socket.js

function inicializarSocket() {
  try {
    const base = (window.APP_BASE || "").replace(/\/+$/, ""); // sin slash final
    const socketPath = base ? `${base}/socket.io` : "/socket.io";

    window.socket = io({
      path: socketPath,
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

    window.socket.on("snapshot_inicial", (data) => {
      console.log("📦 Snapshot recibido:", data);
      aplicarSnapshotInicial(data);
    });

    window.socket.on("evento_nuevo", (data) => {
      console.log("📢 evento_nuevo desde otro cliente:", data);
      agregarFilaEvento(false, data.row || { id: data.id });
    });

    window.socket.on("evento_update", (data) => {
      aplicarUpdateEventoRemoto(data);
    });

    window.socket.on("evento_eliminar", (data) => {
      eliminarFilaEventoRemoto(data);
    });

    window.socket.on("form_update", (data) => {
      aplicarFormUpdateRemoto(data);
    });

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

document.addEventListener("DOMContentLoaded", () => {
  inicializarSocket();
});
