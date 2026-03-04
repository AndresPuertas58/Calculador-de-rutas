console.log("COLTANQUES_APP_V3.0_SPANISH_VERSION");

let mapa;
let capaRuta;
let capaVacio;
let marcadores = [];

// Navegación
function mostrarPestana(pestana) {
    document.querySelectorAll('.sidebar nav li').forEach(li => li.classList.remove('active'));
    const elementoNav = document.getElementById(`nav-${pestana}`);
    if (elementoNav) elementoNav.classList.add('active');

    document.getElementById('tab-dashboard').style.display = pestana === 'dashboard' ? 'block' : 'none';
    document.getElementById('tab-fletes').style.display = pestana === 'fletes' ? 'block' : 'none';
    document.getElementById('tab-vehiculos').style.display = pestana === 'vehiculos' ? 'block' : 'none';
    document.getElementById('tab-conductores').style.display = pestana === 'conductores' ? 'block' : 'none';

    document.getElementById('main-view-container').style.display = 'block';
    document.getElementById('assignment-view').style.display = 'none';

    document.getElementById('page-title').innerText =
        pestana === 'dashboard' ? 'Dashboard' :
            (pestana === 'fletes' ? 'Gestión de Fletes' :
                (pestana === 'vehiculos' ? 'Vehículos' : 'Conductores'));

    if (pestana === 'dashboard' || pestana === 'fletes') obtenerDatosDashboard();
    else if (pestana === 'vehiculos') obtenerVehiculos();
    else if (pestana === 'conductores') obtenerConductores();
}

const Notificacion = Swal.mixin({
    toast: true, position: 'top-end', showConfirmButton: false, timer: 3000
});

async function obtenerDatosDashboard() {
    try {
        const respuesta = await fetch(`http://localhost:5000/api/dashboard?t=${Date.now()}`);
        const datos = await respuesta.json();
        const conteoPendientes = datos.filter(f => (f.estado || "").toLowerCase().trim() === 'sin_asignar').length;

        document.getElementById('total-fletes').innerText = datos.length;
        document.getElementById('total-pendientes').innerText = conteoPendientes;
        document.getElementById('total-vehiculos').innerText = datos.filter(f => f.vehiculo).length;

        renderizarFletes(datos);

        document.getElementById('api-status').innerText = 'En Línea';
        document.getElementById('status-dot').classList.add('online');
    } catch (e) {
        document.getElementById('api-status').innerText = 'Error';
        document.getElementById('status-dot').classList.remove('online');
    }
}

function renderizarFletes(datos) {
    const cuerpoTabla = document.getElementById('fletes-body');
    if (!cuerpoTabla) return;
    cuerpoTabla.innerHTML = '';
    datos.forEach(f => {
        const estadoRaw = (f.estado || "").toLowerCase().trim();
        const esSinAsignar = estadoRaw === 'sin_asignar';
        const esAsignado = estadoRaw === 'asignado' && f.vehiculo;
        const estadoMostrar = (f.estado || "").replace(/_/g, ' ');

        cuerpoTabla.innerHTML += `
            <tr>
                <td><strong>${f.cod_flete}</strong></td>
                <td>${f.cliente}</td>
                <td>${f.producto}</td>
                <td>${f.peso} ton</td>
                <td>${f.punto_carga}</td>
                <td><span class="badge ${esSinAsignar ? 'badge-pending' : 'badge-assigned'}">${estadoMostrar}</span></td>
                <td>
                    <div style="display:flex; flex-direction:column; gap:5px; align-items:flex-start;">
                        ${f.vehiculo ? `<span><i class="fas fa-truck"></i> ${f.vehiculo.placa}</span>` : ''}
                        ${esSinAsignar ?
                `<button class="btn-assign-sm" onclick="abrirVistaAsignacion('${f.cod_flete}')"><i class="fas fa-play"></i> Ejecutar</button>` :
                (esAsignado ? `<button class="btn-unassign-sm" onclick="desasignarCamion('${f.cod_flete}')"><i class="fas fa-times"></i> Desasignar</button>` : '')
            }
                    </div>
                </td>
            </tr>
        `;
    });
}

function inicializarMapa() {
    if (mapa) return;
    mapa = L.map('map').setView([4.5709, -74.2973], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; Coltanques'
    }).addTo(mapa);
}

function mostrarTrayectoCompletoEnMapa(posCamion, puntosVacio, puntosViaje, coordenadasOrigen, coordenadasDestino) {
    inicializarMapa();
    if (capaRuta) mapa.removeLayer(capaRuta);
    if (capaVacio) mapa.removeLayer(capaVacio);
    marcadores.forEach(m => mapa.removeLayer(m));
    marcadores = [];

    document.getElementById('map-placeholder').style.display = 'none';

    // 1. RUTA VACÍO
    const latLngsVacio = puntosVacio.map(p => [p[1], p[0]]);
    capaVacio = L.polyline(latLngsVacio, {
        color: '#4b5563', // Gris más oscuro
        weight: 5,
        opacity: 0.8
    }).addTo(mapa);

    // 2. RUTA CARGADO
    const latLngsViaje = puntosViaje.map(p => [p[1], p[0]]);
    capaRuta = L.polyline(latLngsViaje, {
        color: '#dc2626',
        weight: 6,
        opacity: 1
    }).addTo(mapa);

    // ICONOS
    const iconoCamion = L.divIcon({
        html: '<i class="fas fa-truck" style="color:#111; font-size:20px;"></i>',
        className: 'custom-div-icon', iconSize: [24, 24], iconAnchor: [12, 12]
    });
    const iconoOrigen = L.divIcon({
        html: '<i class="fas fa-map-marker-alt" style="color:#dc2626; font-size:24px;"></i>',
        className: 'custom-div-icon', iconSize: [24, 24], iconAnchor: [12, 24]
    });
    const iconoBandera = L.divIcon({
        html: '<i class="fas fa-flag-checkered" style="color:#111; font-size:24px;"></i>',
        className: 'custom-div-icon', iconSize: [24, 24], iconAnchor: [12, 24]
    });

    // MARCADORES
    marcadores.push(L.marker([posCamion[0], posCamion[1]], { icon: iconoCamion }).addTo(mapa).bindPopup('Ubicación del Camión'));
    marcadores.push(L.marker([coordenadasOrigen[0], coordenadasOrigen[1]], { icon: iconoOrigen }).addTo(mapa).bindPopup('Punto de Carga (Origen)'));
    marcadores.push(L.marker([coordenadasDestino[0], coordenadasDestino[1]], { icon: iconoBandera }).addTo(mapa).bindPopup('Punto de Despacho (Destino)'));

    // Ajustar vista
    const grupo = new L.featureGroup([capaRuta, capaVacio]);
    mapa.fitBounds(grupo.getBounds(), { padding: [70, 70] });
}

async function abrirVistaAsignacion(id) {
    document.getElementById('main-view-container').style.display = 'none';
    document.getElementById('assignment-view').style.display = 'block';

    document.getElementById('map-placeholder').style.display = 'flex';
    document.getElementById('map-placeholder').style.opacity = '1';
    if (capaRuta) mapa.removeLayer(capaRuta);
    if (capaVacio) mapa.removeLayer(capaVacio);
    marcadores.forEach(m => mapa.removeLayer(m));

    const contenedor = document.getElementById('recommendation-container');
    const cargando = document.getElementById('assignment-loading');
    const tarjetaFlete = document.getElementById('flete-detail-card');

    contenedor.innerHTML = '';
    cargando.style.display = 'block';
    tarjetaFlete.style.display = 'none';

    try {
        const respuesta = await fetch(`http://localhost:5000/api/assign/${id}`);
        const datos = await respuesta.json();
        cargando.style.display = 'none';

        const f = datos.flete;
        tarjetaFlete.innerHTML = `
            <div class="flete-main-info">
                <div class="flete-info-item"><small>Cliente</small><p>${f.cliente}</p></div>
                <div class="flete-info-item"><small>Producto</small><p>${f.producto} (${f.peso} ton)</p></div>
                <div class="flete-info-item"><small>Origen</small><p>${f.punto_carga}</p></div>
                <div class="flete-info-item"><small>Destino</small><p>${f.destino}</p></div>
            </div>
        `;
        tarjetaFlete.style.display = 'block';
        inicializarMapa();

        if (!datos.recommendations || datos.recommendations.length === 0) {
            contenedor.innerHTML = '<p class="no-trucks">No se encontraron camiones disponibles.</p>';
            return;
        }

        datos.recommendations.forEach((r, i) => {
            const coordenadasOrigen = f.origen.split(',').map(c => parseFloat(c));
            const coordenadasDestino = f.destino.split(',').map(c => parseFloat(c));

            const posCamion = JSON.stringify(r.truck_pos);
            const puntosVacio = JSON.stringify(r.route_vacio_points);
            const puntosViaje = JSON.stringify(r.route_points);

            contenedor.innerHTML += `
                <div class="rec-card ${i === 0 ? 'best' : ''}">
                    <div class="rec-rank">#${i + 1}</div>
                    <div class="rec-info">
                        <h4>${r.placa} (${r.marca})</h4>
                        <div class="rec-details">
                            <p><i class="fas fa-truck-moving" style="color:#666"></i> <strong>A carga:</strong> ${r.distancia_vacio} km</p>
                            <p><i class="fas fa-route" style="color:var(--primary)"></i> <strong>Viaje:</strong> ${r.distancia_viaje} km</p>
                        </div>
                    </div>
                    <div class="rec-breakdown">
                        <p><strong>Costo Estimado:</strong> $${r.costo_total.toLocaleString()} (${r.costo_peajes.toLocaleString()} en peajes)</p>
                    </div>
                    <div class="rec-final">
                        <button class="btn-assign" onclick="asignarCamion('${id}', '${r.cod_vehiculo}')"><i class="fas fa-check"></i> Asignar</button>
                        <button class="btn-maps" onclick='mostrarTrayectoCompletoEnMapa(${posCamion}, ${puntosVacio}, ${puntosViaje}, [${coordenadasOrigen}], [${coordenadasDestino}])'><i class="fas fa-map-marked-alt"></i> Ver Mapa</button>
                    </div>
                </div>
            `;
        });
    } catch (e) {
        cargando.style.display = 'none';
        Notificacion.fire({ icon: 'error', title: 'Error al conectar con el servidor' });
    }
}

async function asignarCamion(f, v) {
    const resultado = await Swal.fire({
        title: '¿Confirmar asignación?',
        text: `Asignar vehículo ${v} al flete ${f}`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        confirmButtonText: 'Sí, asignar',
        cancelButtonText: 'Cancelar'
    });

    if (!resultado.isConfirmed) return;

    try {
        const respuesta = await fetch('http://localhost:5000/api/assign', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cod_flete: f, cod_vehiculo: v })
        });
        if (respuesta.ok) {
            Swal.fire('¡Asignado!', 'El flete ha sido actualizado correctamente.', 'success');
            volverAlDashboard();
        } else {
            const err = await respuesta.json();
            Swal.fire('Error', err.error, 'error');
        }
    } catch (e) { Swal.fire('Error', 'No se pudo completar la asignación', 'error'); }
}

async function desasignarCamion(id) {
    const resultado = await Swal.fire({
        title: '¿Desasignar vehículo?',
        text: 'El camión volverá a estar disponible.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        confirmButtonText: 'Sí, desasignar',
        cancelButtonText: 'Cancelar'
    });

    if (!resultado.isConfirmed) return;

    try {
        const respuesta = await fetch(`http://localhost:5000/api/unassign/${id}`, { method: 'POST' });
        if (respuesta.ok) {
            Notificacion.fire({ icon: 'success', title: 'Vehículo desasignado' });
            obtenerDatosDashboard();
        } else {
            Swal.fire('Error', 'No se pudo desasignar el vehículo', 'error');
        }
    } catch (e) { Notificacion.fire({ icon: 'error', title: 'Error de conexión' }); }
}

async function obtenerVehiculos() {
    try {
        const respuesta = await fetch('http://localhost:5000/api/vehiculos');
        const datos = await respuesta.json();
        const cuerpoTabla = document.getElementById('vehiculos-body');
        if (!cuerpoTabla) return;
        cuerpoTabla.innerHTML = datos.map(v => `
            <tr>
                <td>${v.cod_vehiculo}</td>
                <td><strong>${v.placa}</strong></td>
                <td>${v.marca}</td>
                <td>${v.color}</td>
                <td>${v.tipo_plancha}</td>
                <td><span class="badge ${v.estado === 'Disponible' ? 'badge-assigned' : 'badge-pending'}">${v.estado}</span></td>
                <td>${v.flete_activo || '-'}</td>
                <td>${v.lat ? v.lat.toFixed(4) : '-'}</td>
            </tr>
        `).join('');
    } catch (e) { Notificacion.fire({ icon: 'error', title: 'Error al cargar vehículos' }); }
}

async function obtenerConductores() {
    try {
        const respuesta = await fetch('http://localhost:5000/api/conductores');
        const datos = await respuesta.json();
        const cuerpoTabla = document.getElementById('conductores-body');
        if (!cuerpoTabla) return;
        cuerpoTabla.innerHTML = datos.map(c => `
            <tr>
                <td>${c.cod_empleado}</td>
                <td><strong>${c.nombre}</strong></td>
                <td>${c.cedula}</td>
                <td><span class="badge badge-assigned" style="background:#111">${c.licencia}</span></td>
                <td>${c.vacaciones}</td>
                <td>${c.incapacidad}</td>
                <td>${c.telefono}</td>
                <td>${c.vehiculo_habitual || '-'}</td>
            </tr>
        `).join('');
    } catch (e) { Notificacion.fire({ icon: 'error', title: 'Error al cargar conductores' }); }
}

function volverAlDashboard() {
    document.getElementById('main-view-container').style.display = 'block';
    document.getElementById('assignment-view').style.display = 'none';
    mostrarPestana('dashboard');
}

document.addEventListener('DOMContentLoaded', () => {
    mostrarPestana('dashboard');
});
