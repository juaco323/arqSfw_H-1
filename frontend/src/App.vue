<script setup>
import { ref } from "vue";

const API_BASE = "http://localhost:8000";

const userName = ref("");
const userEmail = ref("");
const userResult = ref("");

const packageUserId = ref("");
const packageTitle = ref("");
const packageCity = ref("");
const packageLocation = ref("");
const packageResult = ref("");
const lastTrackingCode = ref("");

const updateTrackingCode = ref("");
const updateStatus = ref("IN_TRANSIT");
const updateLocation = ref("");
const updateNote = ref("");
const updateResult = ref("");

const findTrackingCode = ref("");
const trackingResult = ref(null);

async function createUser() {
  userResult.value = "Procesando...";
  try {
    const response = await fetch(`${API_BASE}/createUser`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: userName.value, email: userEmail.value }),
    });
    const data = await response.json();
    if (!response.ok) {
      userResult.value = "Error al crear usuario";
      return;
    }
    packageUserId.value = String(data.user_id || "");
    userResult.value = `Usuario creado: ${data.username} (ID ${data.user_id})`;
  } catch {
    userResult.value = "Error de red al crear usuario";
  }
}

async function createPackage() {
  packageResult.value = "Procesando...";
  try {
    const response = await fetch(`${API_BASE}/createPackage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: parseInt(packageUserId.value, 10),
        package_title: packageTitle.value,
        city: packageCity.value,
        location: packageLocation.value,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      packageResult.value = "Error al crear paquete";
      return;
    }
    lastTrackingCode.value = data.tracking_code || "";
    updateTrackingCode.value = lastTrackingCode.value;
    findTrackingCode.value = lastTrackingCode.value;
    packageResult.value = `Paquete creado: ${lastTrackingCode.value}`;
  } catch {
    packageResult.value = "Error de red al crear paquete";
  }
}

async function setTrackingStatus() {
  updateResult.value = "Procesando...";
  try {
    const response = await fetch(`${API_BASE}/updateStatus`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tracking_code: updateTrackingCode.value,
        new_status: updateStatus.value,
        location: updateLocation.value,
        note: updateNote.value,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      updateResult.value = "Error al actualizar estado";
      return;
    }
    updateResult.value = `Estado actualizado: ${data.status}`;
  } catch {
    updateResult.value = "Error de red al actualizar estado";
  }
}

async function findTracking() {
  trackingResult.value = null;
  try {
    const response = await fetch(
      `${API_BASE}/getTracking/${encodeURIComponent(findTrackingCode.value.trim())}`
    );
    const data = await response.json();
    if (!response.ok) {
      trackingResult.value = { error: true, payload: data };
      return;
    }
    trackingResult.value = data;
  } catch {
    trackingResult.value = { error: true, payload: "Error de red" };
  }
}
</script>

<template>
  <div class="page">
    <header class="hero">
      <h1>Sistema de Tracking</h1>
      <p>Interfaz actualizada para usuario-service, package-service y tracking-service.</p>
    </header>

    <section class="grid">
      <article class="card">
        <h2>1. Crear usuario</h2>
        <label>Nombre</label>
        <input v-model="userName" type="text" />
        <label>Email</label>
        <input v-model="userEmail" type="email" />
        <button @click="createUser">Crear usuario</button>
        <p class="msg">{{ userResult }}</p>
      </article>

      <article class="card">
        <h2>2. Crear paquete</h2>
        <label>ID Usuario</label>
        <input v-model="packageUserId" type="text" />
        <label>Título</label>
        <input v-model="packageTitle" type="text" />
        <label>Ciudad</label>
        <input v-model="packageCity" type="text" />
        <label>Ubicación</label>
        <input v-model="packageLocation" type="text" />
        <button @click="createPackage">Crear paquete</button>
        <p class="msg">{{ packageResult }}</p>
      </article>

      <article class="card">
        <h2>3. Actualizar estado</h2>
        <label>Tracking code</label>
        <input v-model="updateTrackingCode" type="text" />
        <label>Estado</label>
        <select v-model="updateStatus">
          <option>CREATED</option>
          <option>IN_TRANSIT</option>
          <option>OUT_FOR_DELIVERY</option>
          <option>DELIVERED</option>
          <option>EXCEPTION</option>
        </select>
        <label>Ubicación</label>
        <input v-model="updateLocation" type="text" />
        <label>Nota</label>
        <input v-model="updateNote" type="text" />
        <button @click="setTrackingStatus">Actualizar estado</button>
        <p class="msg">{{ updateResult }}</p>
      </article>

      <article class="card card-wide">
        <h2>4. Consultar tracking</h2>
        <label>Tracking code</label>
        <input v-model="findTrackingCode" type="text" />
        <button @click="findTracking">Consultar</button>

        <div v-if="trackingResult" class="result">
          <template v-if="trackingResult.error">
            <p class="error">Error: {{ JSON.stringify(trackingResult.payload) }}</p>
          </template>
          <template v-else>
            <p><strong>Código:</strong> {{ trackingResult.tracking_code }}</p>
            <p><strong>Estado actual:</strong> {{ trackingResult.current_status }}</p>
            <ul>
              <li v-for="(ev, index) in trackingResult.events" :key="index">
                {{ ev.status }} | {{ ev.location }} | {{ ev.note }}
              </li>
            </ul>
          </template>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
:global(body) {
  margin: 0;
  font-family: "Trebuchet MS", "Segoe UI", sans-serif;
  background: radial-gradient(circle at 20% 10%, #f0f8ff 0%, #e5ecf7 55%, #d8e2ef 100%);
  color: #1a2a3a;
}

.page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}

.hero {
  background: #0c4a6e;
  color: #f8fafc;
  border-radius: 14px;
  padding: 18px 22px;
  margin-bottom: 18px;
}

.hero h1 {
  margin: 0 0 4px;
}

.hero p {
  margin: 0;
}

.grid {
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}

.card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #d4deea;
  box-shadow: 0 8px 20px rgba(12, 74, 110, 0.08);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card h2 {
  margin: 0 0 6px;
  font-size: 18px;
}

.card-wide {
  grid-column: 1 / -1;
}

label {
  font-size: 13px;
  color: #3c5064;
}

input,
select {
  border: 1px solid #c6d3e2;
  border-radius: 8px;
  padding: 8px 10px;
}

button {
  margin-top: 6px;
  border: none;
  border-radius: 8px;
  padding: 9px 12px;
  background: #0ea5a8;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

button:hover {
  background: #0c9093;
}

.msg {
  min-height: 18px;
  font-size: 13px;
}

.result {
  margin-top: 8px;
  background: #f8fbff;
  border: 1px solid #d7e4f0;
  border-radius: 8px;
  padding: 10px;
}

.error {
  color: #b42318;
}
</style>
