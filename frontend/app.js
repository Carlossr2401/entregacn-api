// --- 1. CONFIGURACIÓN ---
let API_URL = ""; 

// --- 2. ELEMENTOS DEL DOM ---
const seccionConfig = document.getElementById('seccion-config');
const appContainer = document.getElementById('app-container');
const apiUrlInput = document.getElementById('api-url-input');
const btnLoadApi = document.getElementById('btn-load-api');

const form = document.getElementById('form-nota');
const formTitulo = document.getElementById('form-titulo');
const btnGuardar = document.getElementById('btn-guardar');
const btnCancelar = document.getElementById('btn-cancelar');
const inputId = document.getElementById('edit-note-id');
const inputClase = document.getElementById('clase-nombre');
const inputAlumno = document.getElementById('alumno-nombre');
const inputNota = document.getElementById('nota');
const tablaBody = document.getElementById('lista-notas-tbody');
const jsonContent = document.getElementById('json-content');

// --- 3. EVENT LISTENERS ---
btnLoadApi.addEventListener('click', inicializarApp);
form.addEventListener('submit', handleFormSubmit);
tablaBody.addEventListener('click', handleTableClick);
btnCancelar.addEventListener('click', limpiarFormulario);

// --- 4. FUNCIONES PRINCIPALES ---

/**
 * NUEVO: Se llama al pulsar "Cargar API".
 * Guarda la URL y carga los datos.
 */
async function inicializarApp() {
    const url = apiUrlInput.value.trim();

    if (!url || !url.startsWith('http')) {
        alert("Por favor, introduce una URL de API válida.");
        return;
    }

    API_URL = url.endsWith('/') ? url.slice(0, -1) : url;

    try {
        await cargarNotas();
        
        // --- CAMBIO AQUÍ ---
        // Ya no ocultamos la sección de configuración.
        // seccionConfig.classList.add('hidden'); <-- LÍNEA ELIMINADA
        
        // Pero sí mostramos el contenedor de la app.
        appContainer.classList.remove('hidden');

    } catch (error) {
        console.error("No se pudo conectar a la API:", error);
        alert("Error al cargar la API. Revisa la URL y la consola.");
    }
}

/**
 * Carga todas las notas desde la API y las muestra en la tabla.
 */
async function cargarNotas() {
    tablaBody.innerHTML = '<tr><td colspan="4">Cargando...</td></tr>';
    
    try {
        const response = await fetch(`${API_URL}/notas`); 
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        const notas = await response.json();
        
        tablaBody.innerHTML = ''; 
        
        if (notas.length === 0) {
            tablaBody.innerHTML = '<tr><td colspan="4">No hay notas. ¡Añade una!</td></tr>';
        } else {
            notas.forEach(nota => {
                renderizarFilaNota(nota);
            });
        }
    } catch (error) {
        console.error("Error al cargar notas:", error);
        tablaBody.innerHTML = '<tr><td colspan="4">Error al cargar las notas.</td></tr>';
        throw error;
    }
}

/**
 * Crea una fila (<tr>) en la tabla para una nota.
 * @param {object} nota - El objeto de la nota con AlumnoNombre, ClaseNombre, etc.
 */
function renderizarFilaNota(nota) {
    const id = nota.noteId || nota.NoteID; 
    
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td>${nota.AlumnoNombre}</td>
        <td>${nota.ClaseNombre}</td>
        <td>${nota.Nota}</td>
        <td>
            <button class="btn-accion btn-editar" 
                    data-id="${id}"
                    data-clase="${nota.ClaseNombre}"
                    data-alumno="${nota.AlumnoNombre}"
                    data-nota="${nota.Nota}">
                Editar
            </button>
            <button class="btn-accion btn-borrar" data-id="${id}">
                Borrar
            </button>
            <button class="btn-accion btn-ver-json" data-json='${JSON.stringify(nota)}'>
                JSON
            </button>
        </td>
    `;
    tablaBody.appendChild(tr);
}

/**
 * Decide si crear o actualizar una nota cuando se envía el formulario.
 */
async function handleFormSubmit(e) {
    e.preventDefault();
    const noteId = inputId.value;
    if (noteId) {
        await actualizarNota(noteId);
    } else {
        await crearNota();
    }
}

/**
 * Envía una nueva nota a la API (POST).
 */
async function crearNota() {
    const nuevaNota = {
        ClaseNombre: inputClase.value,
        AlumnoNombre: inputAlumno.value,
        Nota: parseInt(inputNota.value, 10)
    };

    try {
        const response = await fetch(`${API_URL}/notas`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nuevaNota)
        });

        if (!response.ok) {
            if (response.status === 400) {
                const errorData = await response.json();
                alert(`Error al crear: ${JSON.stringify(errorData.errors)}`);
            } else {
                throw new Error(`Error HTTP: ${response.status}`);
            }
        } else {
            limpiarFormulario();
            cargarNotas(); 
        }
    } catch (error) {
        console.error("Error en crearNota:", error);
        alert("No se pudo crear la nota.");
    }
}

/**
 * Actualiza una nota existente en la API (PUT).
 * @param {string} noteId - El ID de la nota a actualizar.
 */
async function actualizarNota(noteId) {
    const notaActualizada = {
        ClaseNombre: inputClase.value,
        AlumnoNombre: inputAlumno.value,
        Nota: parseInt(inputNota.value, 10)
    };

    try {
        const response = await fetch(`${API_URL}/notas/${noteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(notaActualizada)
        });

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        
        limpiarFormulario();
        cargarNotas();
    } catch (error) {
        console.error("Error en actualizarNota:", error);
        alert("No se pudo actualizar la nota.");
    }
}

/**
 * Maneja los clics en los botones de la tabla.
 */
function handleTableClick(e) {
    const boton = e.target;
    const noteId = boton.dataset.id; 

    if (boton.classList.contains('btn-editar')) {
        inputId.value = noteId;
        inputClase.value = boton.dataset.clase;
        inputAlumno.value = boton.dataset.alumno;
        inputNota.value = boton.dataset.nota;
        
        formTitulo.textContent = "Editar Nota";
        btnGuardar.textContent = "Actualizar Nota";
        btnCancelar.classList.remove('hidden');
        window.scrollTo(0, 0); 
    }

    if (boton.classList.contains('btn-borrar')) {
        if (confirm(`¿Estás seguro de que quieres borrar la nota ${noteId}?`)) {
            borrarNota(noteId);
        }
    }

    if (boton.classList.contains('btn-ver-json')) {
        const datosJson = JSON.parse(boton.dataset.json);
        jsonContent.textContent = JSON.stringify(datosJson, null, 2); 
    }
}

/**
 * Borra una nota de la API (DELETE).
 * @param {string} noteId - El ID de la nota a borrar.
 */
async function borrarNota(noteId) {
    if (!noteId) {
        console.error("ID de nota es undefined. No se puede borrar.");
        return;
    }
    try {
        const response = await fetch(`${API_URL}/notas/${noteId}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        cargarNotas(); 
    } catch (error) {
        console.error("Error en borrarNota:", error);
        alert("No se pudo borrar la nota.");
    }
}

/**
 * Limpia el formulario y lo restaura al modo "Crear".
 */
function limpiarFormulario() {
    form.reset();
    inputId.value = '';
    formTitulo.textContent = "Añadir Nueva Nota";
    btnGuardar.textContent = "Guardar Nota";
    btnCancelar.classList.add('hidden');
    jsonContent.textContent = 'Haz clic en el botón "JSON" de una nota para ver los datos completos aquí.';
}