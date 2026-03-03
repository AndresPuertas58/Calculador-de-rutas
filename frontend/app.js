console.log("COLTANQUES_APP_V2.7_FULL_JOURNEY");

let map;
let routeLayer;
let vacioLayer; // New layer for truck -> origin
let markers = [];

// Navigation
function showTab(tab) {
    document.querySelectorAll('.sidebar nav li').forEach(li => li.classList.remove('active'));
    const navEl = document.getElementById(`nav-${tab}`);
    if (navEl) navEl.classList.add('active');

    document.getElementById('tab-dashboard').style.display = tab === 'dashboard' ? 'block' : 'none';
    document.getElementById('tab-fletes').style.display = tab === 'fletes' ? 'block' : 'none';
    document.getElementById('tab-vehiculos').style.display = tab === 'vehiculos' ? 'block' : 'none';
    document.getElementById('tab-conductores').style.display = tab === 'conductores' ? 'block' : 'none';

    document.getElementById('main-view-container').style.display = 'block';
    document.getElementById('assignment-view').style.display = 'none';

    document.getElementById('page-title').innerText =
        tab === 'dashboard' ? 'Dashboard' :
            (tab === 'fletes' ? 'Gestión de Fletes' :
                (tab === 'vehiculos' ? 'Vehículos' : 'Conductores'));

    if (tab === 'dashboard' || tab === 'fletes') fetchDashboardData();
    else if (tab === 'vehiculos') fetchVehiculos();
    else if (tab === 'conductores') fetchConductores();
}

const Toast = Swal.mixin({
    toast: true, position: 'top-end', showConfirmButton: false, timer: 3000
});

async function fetchDashboardData() {
    try {
        const res = await fetch(`http://localhost:5000/api/dashboard?t=${Date.now()}`);
        const data = await res.json();
        const pendCount = data.filter(f => (f.estado || "").toLowerCase().trim() === 'sin_asignar').length;

        document.getElementById('total-fletes').innerText = data.length;
        document.getElementById('total-pendientes').innerText = pendCount;
        document.getElementById('total-vehiculos').innerText = data.filter(f => f.vehiculo).length;

        renderFletes(data);

        document.getElementById('api-status').innerText = 'Online';
        document.getElementById('status-dot').classList.add('online');
    } catch (e) {
        document.getElementById('api-status').innerText = 'Error';
        document.getElementById('status-dot').classList.remove('online');
    }
}

function renderFletes(data) {
    const body = document.getElementById('fletes-body');
    if (!body) return;
    body.innerHTML = '';
    data.forEach(f => {
        const rawState = (f.estado || "").toLowerCase().trim();
        const isSinAsignar = rawState === 'sin_asignar';
        const isAsignado = rawState === 'asignado' && f.vehiculo;
        const displayState = (f.estado || "").replace(/_/g, ' ');

        body.innerHTML += `
            <tr>
                <td><strong>${f.cod_flete}</strong></td>
                <td>${f.cliente}</td>
                <td>${f.producto}</td>
                <td>${f.peso} ton</td>
                <td>${f.punto_carga}</td>
                <td><span class="badge ${isSinAsignar ? 'badge-pending' : 'badge-assigned'}">${displayState}</span></td>
                <td>
                    <div style="display:flex; flex-direction:column; gap:5px; align-items:flex-start;">
                        ${f.vehiculo ? `<span><i class="fas fa-truck"></i> ${f.vehiculo.placa}</span>` : ''}
                        ${isSinAsignar ?
                `<button class="btn-assign-sm" onclick="openAssignmentView('${f.cod_flete}')"><i class="fas fa-play"></i> Ejecutar</button>` :
                (isAsignado ? `<button class="btn-unassign-sm" onclick="unassignTruck('${f.cod_flete}')"><i class="fas fa-times"></i> Desasignar</button>` : '')
            }
                    </div>
                </td>
            </tr>
        `;
    });
}

function initMap() {
    if (map) return;
    map = L.map('map').setView([4.5709, -74.2973], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; Coltanques'
    }).addTo(map);
}

function showFullJourneyOnMap(truckPos, originPoints, tripPoints, originCoords, destCoords) {
    initMap();
    if (routeLayer) map.removeLayer(routeLayer);
    if (vacioLayer) map.removeLayer(vacioLayer);
    markers.forEach(m => map.removeLayer(m));
    markers = [];

    document.getElementById('map-placeholder').style.display = 'none';

    // 1. DIBUJAR RUTA VACÍO (Camión -> Origen)
    const vacioLatLngs = originPoints.map(p => [p[1], p[0]]);
    vacioLayer = L.polyline(vacioLatLngs, {
        color: '#6b7280', // Gris
        weight: 4,
        opacity: 0.6,
        dashArray: '10, 10'
    }).addTo(map);

    // 2. DIBUJAR RUTA CARGADO (Origen -> Destino)
    const tripLatLngs = tripPoints.map(p => [p[1], p[0]]);
    routeLayer = L.polyline(tripLatLngs, {
        color: '#dc2626', // Rojo
        weight: 6,
        opacity: 1
    }).addTo(map);

    // ICONOS
    const truckIcon = L.divIcon({
        html: '<i class="fas fa-truck" style="color:#111; font-size:20px;"></i>',
        className: 'custom-div-icon', iconSize: [24, 24], iconAnchor: [12, 12]
    });
    const originIcon = L.divIcon({
        html: '<i class="fas fa-map-marker-alt" style="color:#dc2626; font-size:24px;"></i>',
        className: 'custom-div-icon', iconSize: [24, 24], iconAnchor: [12, 24]
    });
    const flagIcon = L.divIcon({
        html: '<i class="fas fa-flag-checkered" style="color:#111; font-size:24px;"></i>',
        className: 'custom-div-icon', iconSize: [24, 24], iconAnchor: [12, 24]
    });

    // MARCADORES
    markers.push(L.marker([truckPos[0], truckPos[1]], { icon: truckIcon }).addTo(map).bindPopup('Ubicación del Camión'));
    markers.push(L.marker([originCoords[0], originCoords[1]], { icon: originIcon }).addTo(map).bindPopup('Punto de Carga (Origen)'));
    markers.push(L.marker([destCoords[0], destCoords[1]], { icon: flagIcon }).addTo(map).bindPopup('Punto de Despacho (Destino)'));

    // Ajustar vista para ver TODO
    const group = new L.featureGroup([routeLayer, vacioLayer]);
    map.fitBounds(group.getBounds(), { padding: [70, 70] });
}

async function openAssignmentView(id) {
    document.getElementById('main-view-container').style.display = 'none';
    document.getElementById('assignment-view').style.display = 'block';

    document.getElementById('map-placeholder').style.display = 'flex';
    document.getElementById('map-placeholder').style.opacity = '1';
    if (routeLayer) map.removeLayer(routeLayer);
    if (vacioLayer) map.removeLayer(vacioLayer);
    markers.forEach(m => map.removeLayer(m));

    const container = document.getElementById('recommendation-container');
    const loading = document.getElementById('assignment-loading');
    const fleteCard = document.getElementById('flete-detail-card');

    container.innerHTML = '';
    loading.style.display = 'block';
    fleteCard.style.display = 'none';

    try {
        const res = await fetch(`http://localhost:5000/api/assign/${id}`);
        const data = await res.json();
        loading.style.display = 'none';

        const f = data.flete;
        fleteCard.innerHTML = `
            <div class="flete-main-info">
                <div class="flete-info-item"><small>Cliente</small><p>${f.cliente}</p></div>
                <div class="flete-info-item"><small>Producto</small><p>${f.producto} (${f.peso} ton)</p></div>
                <div class="flete-info-item"><small>Origen</small><p>${f.punto_carga}</p></div>
                <div class="flete-info-item"><small>Destino</small><p>${f.destino}</p></div>
            </div>
        `;
        fleteCard.style.display = 'block';
        initMap();

        if (!data.recommendations || data.recommendations.length === 0) {
            container.innerHTML = '<p class="no-trucks">No se encontraron camiones disponibles.</p>';
            return;
        }

        data.recommendations.forEach((r, i) => {
            const originCoords = f.origen.split(',').map(c => parseFloat(c));
            const destCoords = f.destino.split(',').map(c => parseFloat(c));

            // Pasamos todos los datos necesarios para el mapa
            const truckPos = JSON.stringify(r.truck_pos);
            const vacioPoints = JSON.stringify(r.route_vacio_points);
            const tripPoints = JSON.stringify(r.route_points);

            container.innerHTML += `
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
                        <button class="btn-assign" onclick="assignTruck('${id}', '${r.cod_vehiculo}')"><i class="fas fa-check"></i> Asignar</button>
                        <button class="btn-maps" onclick='showFullJourneyOnMap(${truckPos}, ${vacioPoints}, ${tripPoints}, [${originCoords}], [${destCoords}])'><i class="fas fa-map-marked-alt"></i> Ver Mapa</button>
                    </div>
                </div>
            `;
        });
    } catch (e) {
        loading.style.display = 'none';
        Toast.fire({ icon: 'error', title: 'Error al conectar con el servidor' });
    }
}

async function assignTruck(f, v) {
    const result = await Swal.fire({
        title: '¿Confirmar asignación?',
        text: `Asignar vehículo ${v} al flete ${f}`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        confirmButtonText: 'Sí, asignar',
        cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
        const res = await fetch('http://localhost:5000/api/assign', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cod_flete: f, cod_vehiculo: v })
        });
        if (res.ok) {
            Swal.fire('¡Asignado!', 'El flete ha sido actualizado correctamente.', 'success');
            showDashboard();
        } else {
            const err = await res.json();
            Swal.fire('Error', err.error, 'error');
        }
    } catch (e) { Swal.fire('Error', 'No se pudo completar la asignación', 'error'); }
}

async function unassignTruck(id) {
    const result = await Swal.fire({
        title: '¿Desasignar vehículo?',
        text: 'El camión volverá a estar disponible.',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc2626',
        confirmButtonText: 'Sí, desasignar',
        cancelButtonText: 'Cancelar'
    });

    if (!result.isConfirmed) return;

    try {
        const res = await fetch(`http://localhost:5000/api/unassign/${id}`, { method: 'POST' });
        if (res.ok) {
            Toast.fire({ icon: 'success', title: 'Vehículo desasignado' });
            fetchDashboardData();
        } else {
            Swal.fire('Error', 'No se pudo desasignar el vehículo', 'error');
        }
    } catch (e) { Toast.fire({ icon: 'error', title: 'Error de conexión' }); }
}

function showDashboard() {
    document.getElementById('main-view-container').style.display = 'block';
    document.getElementById('assignment-view').style.display = 'none';
    showTab('dashboard');
}

document.addEventListener('DOMContentLoaded', () => {
    showTab('dashboard');
});
