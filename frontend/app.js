// --- CONFIGURACIÓN DINÁMICA ---
// La URL de la API se toma desde el input del HTML
const APIInput = document.getElementById('api-url');
// El input de contraseña y la API Key han sido eliminados, no son necesarios.

// Referencias a los elementos del DOM
const form = document.getElementById('form-crear-nota');
const listaNotas = document.getElementById('lista-notas');

/**
 * 1. Cargar y mostrar todas las notas (GET ALL)
 */
async function cargarNotas() {
    const API_URL = APIInput.value.trim();
    if (!API_URL) {
        listaNotas.innerHTML = '<li>Introduce la URL del endpoint (ej. .../grades).</li>';
        return;
    }

    try {
        console.log(API_URL)
        const response = await fetch(API_URL, {
            method: 'GET'
            // No se necesita encabezado x-api-key
        });
        

        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status} ${response.statusText}`);
        }

        const notas = await response.json();
        listaNotas.innerHTML = '';

        if (notas.length === 0) {
            listaNotas.innerHTML = '<li>No hay notas registradas.</li>';
            return;
        }

        notas.forEach(nota => {
            const item = document.createElement('li');

            const info = document.createElement('div');
            info.className = 'nota-info';
            info.innerHTML = `
                <span>${nota.ClaseNombre}</span> (${nota.AlumnoNombre}) - 
                <strong>Nota: ${nota.Nota}</strong>
            `;

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.innerText = 'Borrar 🗑️';
            deleteBtn.dataset.id = nota.NoteID;

            item.appendChild(info);
            item.appendChild(deleteBtn);
            listaNotas.appendChild(item);
        });

    } catch (error) {
        console.error('Error al cargar notas:', error);
        listaNotas.innerHTML = `<li>Error al cargar las notas: ${error.message}. Revisa la consola y la URL.</li>`;
    }
}

/**
 * 2. Crear una nueva nota (POST)
 */
async function crearNota(e) {
    e.preventDefault();
    const API_URL = APIInput.value.trim();

    if (!API_URL) {
        alert('Introduce la URL del endpoint (ej. .../grades) antes de crear una nota.');
        return;
    }

    const clase = document.getElementById('clase').value;
    const alumno = document.getElementById('alumno').value;
    const nota = document.getElementById('nota').value;

    const nuevaNota = { ClaseNombre: clase, AlumnoNombre: alumno, Nota: nota };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
                // No se necesita encabezado x-api-key
            },
            body: JSON.stringify(nuevaNota)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.details || `Error HTTP: ${response.status}`);
        }

        form.reset();
        cargarNotas();

    } catch (error) {
        console.error('Error al crear la nota:', error);
        alert(`Error al guardar: ${error.message}`);
    }
}

/**
 * 3. Borrar una nota (DELETE)
 */
async function borrarNota(e) {
    if (!e.target.classList.contains('delete-btn')) return;

    const API_URL = APIInput.value.trim();

    if (!API_URL) {
        alert('Introduce la URL del endpoint (ej. .../grades) antes de borrar una nota.');
        return;
    }

    const idParaBorrar = e.target.dataset.id;
    if (!confirm(`¿Seguro que quieres borrar la nota con ID: ${idParaBorrar}?`)) return;

    try {
        // La URL de borrado es la API_URL (que es .../grades) + / + id
        const response = await fetch(`${API_URL}/${idParaBorrar}`, {
            method: 'DELETE'
            // No se necesita encabezado x-api-key
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error HTTP: ${response.status}`);
        }

        cargarNotas();
    } catch (error) {
        console.error('Error al borrar nota:', error);
        alert(`Error al borrar: ${error.message}`);
    }
}

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', cargarNotas);
form.addEventListener('submit', crearNota);
listaNotas.addEventListener('click', borrarNota);