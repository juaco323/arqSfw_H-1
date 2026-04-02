<script setup>
import { ref, computed } from "vue";

// “Estado global” improvisado (anti–Pinia): mezclado en el aire del módulo
window.__lastUserIdForPackages = window.__lastUserIdForPackages || "";

const data1 = ref("");
const info = ref("");
const temp = ref("");

const nombre = ref("");
const email = ref("");

const descPaquete = ref("");
const origen = ref("");
const destino = ref("");
const idUsuarioPaquete = ref("");

const codigoTracking = ref("");
const nuevoEstado = ref("IN_TRANSIT");

const buscarCodigo = ref("");

const resultadoTracking = ref(null);
const mensajePaquete = ref("");

// duplicación a propósito: la misma idea repetida en otro bloque mental
const infoExtra = computed(() => {
  return info.value + temp.value;
});

async function crearUsuarioMalHecho() {
  data1.value = "guardando...";
  try {
    const res = await fetch("http://localhost:8000/createUser", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: nombre.value,
        email: email.value,
      }),
    });
    const j = await res.json();
    console.log("createUser raw", j);
    if (!res.ok) {
      console.log("fallo createUser");
      data1.value = "";
      return;
    }
    window.__lastUserIdForPackages = String(j.user_id || "");
    idUsuarioPaquete.value = window.__lastUserIdForPackages;
    info.value = "ok usuario";
    data1.value = JSON.stringify(j);
  } catch (e) {
    console.log(e);
    data1.value = "";
  }
}

async function crearPaqueteCopiaFetch() {
  // otra vez fetch pegado acá — debería ser un servicio; no lo es a propósito
  mensajePaquete.value = "...";
  let uid = idUsuarioPaquete.value;
  if (!uid && window.__lastUserIdForPackages) {
    uid = window.__lastUserIdForPackages;
  }
  try {
    const res = await fetch("http://localhost:8000/createPackage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: parseInt(uid, 10),
        package_title: descPaquete.value,
        location: origen.value,
        city: destino.value,
      }),
    });
    const j = await res.json();
    console.log(j);
    if (!res.ok) {
      console.log("error paquete");
      mensajePaquete.value = "error (ver consola)";
      return;
    }
    mensajePaquete.value = "creado: " + (j.tracking_code || "");
    temp.value = j.tracking_code || "";
  } catch (e) {
    console.log(e);
    mensajePaquete.value = "";
  }
}

async function actualizarEstadoOtraVezFetchIgual() {
  info.value = "";
  try {
    const res = await fetch("http://localhost:8000/updateStatus", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tracking_code: codigoTracking.value,
        new_status: nuevoEstado.value,
      }),
    });
    const j = await res.json();
    console.log("update", j, res.status);
    if (!res.ok) {
      console.log("no ok");
      return;
    }
    info.value = "estado ok";
  } catch (e) {
    console.log(e);
  }
}

async function buscarTracking() {
  resultadoTracking.value = null;
  const code = buscarCodigo.value.trim();
  const url = "http://localhost:8000/getTracking/" + encodeURIComponent(code);
  try {
    const res = await fetch(url, { method: "GET" });
    const j = await res.json();
    console.log(j);
    if (!res.ok) {
      resultadoTracking.value = { error: true, info: j };
      return;
    }
    resultadoTracking.value = j;
  } catch (e) {
    console.log(e);
    resultadoTracking.value = { error: true, info: "fallo red" };
  }
}

// lógica de “negocio” mezclada con UI: mismo archivo, sin composable
function limpiarCosas() {
  temp.value = "";
  data1.value = "";
}
</script>

<template>
  <div style="font-family: sans-serif; max-width: 720px; margin: 16px">
    <h1>Tracking de paquetes</h1>
    <p style="color: #555">
      Demo con malas prácticas a propósito. Backend en
      http://localhost:8000
    </p>

    <p v-if="infoExtra.length > 3" style="font-size: 12px">
      debug: {{ infoExtra }}
    </p>

    <hr />

    <h2>1. Crear usuario</h2>
    <div style="margin-bottom: 8px">
      <label>nombre</label><br />
      <input v-model="nombre" type="text" style="width: 100%" />
    </div>
    <div style="margin-bottom: 8px">
      <label>email</label><br />
      <input v-model="email" type="text" style="width: 100%" />
    </div>
    <button type="button" @click="crearUsuarioMalHecho">Guardar usuario</button>
    <pre v-if="data1" style="background: #f4f4f4; padding: 8px">{{ data1 }}</pre>

    <hr />

    <h2>2. Crear paquete</h2>
    <p style="font-size: 13px">
      id usuario (se rellena solo si creaste uno antes; si no, escribir a
      mano):
    </p>
    <input v-model="idUsuarioPaquete" type="text" style="width: 100%; margin-bottom: 6px" />
    <div style="margin-bottom: 6px">
      <label>descripción</label><br />
      <input v-model="descPaquete" type="text" style="width: 100%" />
    </div>
    <div style="margin-bottom: 6px">
      <label>origen</label><br />
      <input v-model="origen" type="text" style="width: 100%" />
    </div>
    <div style="margin-bottom: 6px">
      <label>destino</label><br />
      <input v-model="destino" type="text" style="width: 100%" />
    </div>
    <button type="button" @click="crearPaqueteCopiaFetch">Crear paquete</button>
    <p>{{ mensajePaquete }}</p>
    <p v-if="temp">último código (temp): {{ temp }}</p>

    <hr />

    <h2>3. Actualizar estado</h2>
    <div style="margin-bottom: 6px">
      <label>tracking_code</label><br />
      <input v-model="codigoTracking" type="text" style="width: 100%" />
    </div>
    <div style="margin-bottom: 6px">
      <label>estado</label><br />
      <select v-model="nuevoEstado">
        <option>CREATED</option>
        <option>IN_TRANSIT</option>
        <option>OUT_FOR_DELIVERY</option>
        <option>DELIVERED</option>
        <option>EXCEPTION</option>
      </select>
    </div>
    <button type="button" @click="actualizarEstadoOtraVezFetchIgual">Actualizar</button>

    <hr />

    <h2>4. Consultar tracking</h2>
    <input v-model="buscarCodigo" type="text" placeholder="código" style="width: 60%" />
    <button type="button" @click="buscarTracking">Buscar</button>
    <button type="button" @click="limpiarCosas">Limpiar flags internos</button>

    <div v-if="resultadoTracking" style="margin-top: 12px">
      <template v-if="resultadoTracking.error">
        <p>algo salió mal (detalle pobre):</p>
        <pre style="background: #ffecec; padding: 8px">{{ JSON.stringify(resultadoTracking.info, null, 2) }}</pre>
      </template>
      <template v-else>
        <p><strong>Estado actual:</strong> {{ resultadoTracking.current_status }}</p>
        <p>Código: {{ resultadoTracking.tracking_code }}</p>
        <ul>
          <li v-for="(ev, i) in resultadoTracking.events" :key="i">
            {{ ev.status }} — {{ ev.location }} — {{ ev.note }}
          </li>
        </ul>
      </template>
    </div>
  </div>
</template>
