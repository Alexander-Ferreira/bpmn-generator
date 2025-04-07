class BPMNViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) throw new Error(`Contenedor #${containerId} no encontrado`);
        
        this.viewer = new BpmnJS({ 
            container: `#${containerId}`,
            keyboard: { bindTo: document } // Permitir zoom con rueda del mouse
        });
        
        this.currentBPMN = null;
        this.initControls();
    }

    initControls() {
        const controls = document.createElement('div');
        controls.className = 'bpmn-controls';
        controls.innerHTML = `
            <button class="control-button zoom-in">+</button>
            <button class="control-button zoom-out">-</button>
            <button class="control-button download-xml">
                <svg class="download-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Descargar XML
            </button>
        `;
        this.container.appendChild(controls);

        // Event listeners
        controls.querySelector('.zoom-in').addEventListener('click', () => this.zoom(0.1));
        controls.querySelector('.zoom-out').addEventListener('click', () => this.zoom(-0.1));
        controls.querySelector('.download-xml').addEventListener('click', () => this.downloadXML());
    }

    async renderDiagram(xml) {
        try {
            this.currentBPMN = xml;
            await this.viewer.importXML(xml);
            this.viewer.get('canvas').zoom('fit-viewport');
            return true;
        } catch (err) {
            console.error("Error rendering BPMN:", err);
            this.currentBPMN = null;
            throw new Error("No se pudo cargar el diagrama");
        }
    }

    zoom(step) {
        if (this.viewer) {
            this.viewer.get('zoomScroll').stepZoom(step);
        }
    }

    downloadXML() {
        if (!this.currentBPMN) {
            this.showError("No hay diagrama generado para descargar");
            return;
        }
    
        try {
            const description = document.getElementById('description')?.value.trim() || 'diagrama';
            const sanitizedDesc = description
                .substring(0, 30)
                .replace(/[^a-z0-9áéíóúñü\s-]/gi, '')
                .replace(/\s+/g, '-');
    
            const dateStr = new Date().toISOString().slice(0, 10);
            const filename = `bpmn-${dateStr}-${sanitizedDesc}.bpmn`;
    
            const blob = new Blob([this.currentBPMN], { type: 'application/xml' });
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            
            document.body.appendChild(a);
            a.click();
            
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);
        } catch (error) {
            console.error("Error descargando XML:", error);
            this.showError("Error al descargar el archivo");
        }
    }
}

class BPMNApp {
    constructor() {
        try {
            this.bpmnViewer = new BPMNViewer('bpmn-container');
            this.initUIElements();
            this.initEventListeners();
            this.setupKeyboardShortcuts();
        } catch (error) {
            console.error("Error inicializando la app:", error);
            this.showFatalError("No se pudo inicializar el visor BPMN");
        }
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                this.generateDiagram();
            }
        });
    }

    initUIElements() {
        this.ui = {
            description: document.getElementById('description'),
            generateBtn: document.getElementById('generate-btn'),
            buttonText: document.getElementById('button-text'),
            spinner: document.getElementById('spinner'),
            errorMsg: document.getElementById('error-message')
        };
    }

    initEventListeners() {
        this.ui.generateBtn.addEventListener('click', () => this.generateDiagram());
    }

    async generateDiagram() {
        const MIN_DESCRIPTION_LENGTH = 20;
        const description = this.ui.description.value.trim();
        
        if (!description || description.length < MIN_DESCRIPTION_LENGTH) {
            this.showError(`La descripción debe tener al menos ${MIN_DESCRIPTION_LENGTH} caracteres`);
            return;
        }
    
        this.toggleLoading(true);
        this.hideError();
    
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json' // Para forzar JSON
                },
                body: JSON.stringify({ description })
            });
    
            // Manejo de errores
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                const errorText = await response.text();
                throw new Error(`El servidor respondió con: ${errorText.substring(0, 100)}...`);
            }
    
    
            const { bpmn } = await response.json();
            await this.bpmnViewer.renderDiagram(bpmn);
        } catch (error) {
            this.showError(error.message);
            console.error("Error generando diagrama:", error);
        } finally {
            this.toggleLoading(false);
        }
    }

    toggleLoading(loading) {
        if (loading) {
            this.ui.buttonText.textContent = "Generando...";
            this.ui.spinner.style.display = "block";
            this.ui.generateBtn.disabled = true;
        } else {
            this.ui.buttonText.textContent = "Generar Diagrama";
            this.ui.spinner.style.display = "none";
            this.ui.generateBtn.disabled = false;
        }
    }

    showError(message) {
        this.ui.errorMsg.textContent = message;
        this.ui.errorMsg.style.display = "block";
    }

    hideError() {
        this.ui.errorMsg.style.display = "none";
    }
}

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    new BPMNApp();
});

async function generateBPMN(description) {
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ description })
        });

        // Verifica el contenido 
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const errorText = await response.text();
            throw new Error(`El servidor respondió con: ${errorText.substring(0, 100)}...`);
        }

        const { bpmn } = await response.json();
        await this.bpmnViewer.renderDiagram(bpmn);
        
    } catch (error) {
        console.error("Error en generar diagrama:", error);
        this.showError(error.message);
    } finally {
        this.toggleLoading(false);
    }
}
     console.error('Error:', error);

        // Mostrar error 
    async function generateDiagram() {
            const MIN_DESCRIPTION_LENGTH = 20;
            const description = this.ui.description.value.trim();
            
            if (!description || description.length < MIN_DESCRIPTION_LENGTH) {
                this.showError(`La descripción debe tener al menos ${MIN_DESCRIPTION_LENGTH} caracteres`);
                return;
            }
        
            this.toggleLoading(true);
            this.hideError();
        
            try {
                console.log("Enviando solicitud a /api/generate...");
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ description })
                });
    
                console.log("Respuesta recibida. Status:", response.status);
                
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error("Error del servidor:", errorText);
                    throw new Error(`Error del servidor: ${errorText.substring(0, 100)}`);
                }
    
                const result = await response.json();
                console.log("Datos recibidos:", result);
                
                if (!result.bpmn) {
                    throw new Error("El servidor no devolvió un diagrama válido");
                }
                
                await this.bpmnViewer.renderDiagram(result.bpmn);
                
            } catch (error) {
                console.error("Error en generar diagrama:", error);
                this.showError(error.message);
            } finally {
                this.toggleLoading(false);
            }
        }


function showRateLimitMessage(data) {
    Swal.fire({
        icon: 'warning',
        title: '¡Muy rápido!',
        html: `
            <p>${data.error}</p>
            <p><b>${data.solucion}</b></p>
            ${data.reintentar_en ? `<p>Puedes reintentar en: ${data.reintentar_en}</p>` : ''}
        `,
        confirmButtonText: 'Entendido'
    });
}
const apiUrl = 'http://localhost:5000/api/generate';

fetch(apiUrl, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    description: "Tu descripción del proceso aquí..."
  })
})
.then(response => {
  const contentType = response.headers.get('content-type');
  if (!contentType || !contentType.includes('application/json')) {
    return response.text().then(text => {
      throw new Error(`Respuesta no JSON: ${text.substring(0, 100)}...`);
    });
  }
  return response.json();
})
.then(data => console.log(data))
.catch(error => console.error('Error:', error));


console.log("URL de la API:", '/api/generate');
console.log("Descripción enviada:", description);


console.log("Respuesta completa:", {
    status: response.status,
    headers: [...response.headers.entries()],
    body: await response.clone().text()  //para poder leerlo después
});