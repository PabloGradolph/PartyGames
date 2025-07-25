class PartidaWebSocket {
    constructor(codigoPartida) {
        this.codigoPartida = codigoPartida;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1 segundo
        this.init();
    }

    init() {
        this.connect();
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/partida/${this.codigoPartida}/`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = (event) => {
            console.log('WebSocket conectado');
            this.reconnectAttempts = 0;
            this.showConnectionStatus('Conectado', 'success');
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onclose = (event) => {
            console.log('WebSocket desconectado');
            this.showConnectionStatus('Desconectado', 'danger');
            
            // Intentar reconectar si no fue un cierre intencional
            if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => {
                    this.connect();
                }, this.reconnectDelay * this.reconnectAttempts);
            }
        };

        this.socket.onerror = (error) => {
            console.error('Error en WebSocket:', error);
            this.showConnectionStatus('Error de conexión', 'danger');
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'partida_updated':
                this.updatePartidaUI(data.data);
                break;
            case 'user_connected':
                this.showNotification(`${data.username} se ha unido a la partida`, 'success');
                break;
            case 'user_disconnected':
                this.showNotification(`${data.username} se ha desconectado`, 'warning');
                break;
            case 'jugador_eliminado':
                this.showNotification('Un jugador ha sido eliminado', 'danger');
                // Solicitar actualización inmediata de los datos
                setTimeout(() => {
                    this.requestRefresh();
                }, 200);
                break;
            case 'jugador_expulsado':
                this.showNotification('Un jugador ha sido expulsado de la partida', 'warning');
                // Recargar la página para mostrar la información actualizada
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                break;
            case 'partida_iniciada':
                this.showNotification(data.message, 'success');
                // Recargar la página para mostrar la nueva interfaz completa
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                break;
            case 'nueva_ronda_iniciada':
                this.showNotification(data.message, 'success');
                // Recargar la página para mostrar la nueva interfaz completa
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
                break;
            case 'partida_terminada':
                this.showNotification(data.message, 'warning');
                // Redirigir al inicio después de 3 segundos
                setTimeout(() => {
                    window.location.href = '/';
                }, 3000);
                break;
            case 'error':
                this.showNotification(data.message, 'danger');
                break;
            case 'ronda_terminada':
                this.showNotification(data.message, 'warning');
                // Recargar la página para mostrar el estado de ronda terminada
                setTimeout(() => {
                    window.location.reload();
                }, 2000);
                break;
            case 'adivinacion_resultado':
                if (data.resultado.error) {
                    this.showNotification(data.resultado.error, 'danger');
                } else {
                    this.showNotification(data.resultado.mensaje, data.resultado.correcto ? 'success' : 'warning');
                    if (data.resultado.ronda_terminada) {
                        // Recargar la página si la ronda terminó
                        setTimeout(() => {
                            window.location.reload();
                        }, 3000);
                    }
                }
                break;
            default:
                break;
        }
    }

    // Esta función está duplicada, se elimina

    updatePuntuacionTable(jugadores) {
        const tbody = document.querySelector('#puntuacion-table tbody');
        if (!tbody) return;

        tbody.innerHTML = '';
        
        jugadores.forEach(jugador => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>
                    ${jugador.username}
                    ${jugador.es_host ? '<span class="badge bg-success ms-2">Host</span>' : ''}
                </td>
                <td><span class="badge bg-warning points">${jugador.puntos}</span></td>
                <td>${jugador.ronda_actual}</td>
            `;
            tbody.appendChild(row);
        });
    }

    updatePlayerCounters(partidaData) {
        // Actualizar contadores en la UI
        const activosElement = document.querySelector('#jugadores-activos-count');
        const eliminadosElement = document.querySelector('#jugadores-eliminados-count');
        
        if (activosElement) {
            activosElement.textContent = partidaData.jugadores_activos;
        }
        if (eliminadosElement) {
            eliminadosElement.textContent = partidaData.jugadores_eliminados;
        }
    }

    updateGameState(partidaData) {
        // Actualizar estado del juego
        const estadoElement = document.querySelector('#estado-partida');
        if (estadoElement) {
            estadoElement.textContent = partidaData.estado === 'en_juego' ? 'En juego' : 'Esperando';
        }

        // Mostrar/ocultar tabla de puntuaciones según el estado
        const puntuacionRow = document.querySelector('.row.mb-4');
        if (puntuacionRow) {
            if (partidaData.estado === 'en_juego') {
                puntuacionRow.style.display = 'block';
            } else {
                puntuacionRow.style.display = 'none';
            }
        }

        // Mostrar/ocultar elementos según el estado
        const botonesJuego = document.querySelectorAll('.boton-juego');
        botonesJuego.forEach(boton => {
            if (partidaData.estado === 'en_juego') {
                boton.style.display = 'inline-block';
            } else {
                boton.style.display = 'none';
            }
        });

        // Actualizar botón "Empezar partida" basado en el número de jugadores
        this.updateStartButton(partidaData);
    }

    updateStartButton(partidaData) {
        // Buscar el contenedor de controles del host
        const hostControls = document.querySelector('.mt-4');
        if (!hostControls) return;

        // Buscar elementos existentes
        let startButton = hostControls.querySelector('#start-game-button');
        let warningDiv = hostControls.querySelector('#warning-message');

        // Limpiar elementos existentes si no tienen los IDs correctos
        const oldButtons = hostControls.querySelectorAll('button[onclick*="iniciarPartida"]');
        const oldWarnings = hostControls.querySelectorAll('.alert-warning');
        
        oldButtons.forEach(btn => {
            if (!btn.id) btn.remove();
        });
        oldWarnings.forEach(warn => {
            if (!warn.id) warn.remove();
        });

        if (partidaData.jugadores_activos >= 4 && partidaData.estado !== 'en_juego') {
            // Ocultar mensaje de advertencia si existe
            if (warningDiv) {
                warningDiv.style.display = 'none';
            }
            
            // Crear o mostrar botón de empezar partida
            if (!startButton) {
                startButton = document.createElement('button');
                startButton.id = 'start-game-button';
                startButton.type = 'button';
                startButton.className = 'btn btn-success mt-2';
                startButton.onclick = () => this.iniciarPartida();
                startButton.textContent = 'Empezar partida';
                hostControls.appendChild(startButton);
            } else {
                startButton.style.display = 'inline-block';
            }
        } else if (partidaData.estado !== 'en_juego') {
            // Ocultar botón si existe
            if (startButton) {
                startButton.style.display = 'none';
            }
            
            // Crear o mostrar mensaje de advertencia
            if (!warningDiv) {
                warningDiv = document.createElement('div');
                warningDiv.id = 'warning-message';
                warningDiv.className = 'alert alert-warning mt-2';
                warningDiv.textContent = 'Se necesitan al menos 4 jugadores para empezar la partida.';
                hostControls.appendChild(warningDiv);
            } else {
                warningDiv.style.display = 'block';
            }
        } else {
            // Si la partida está en juego, ocultar ambos
            if (startButton) {
                startButton.style.display = 'none';
            }
            if (warningDiv) {
                warningDiv.style.display = 'none';
            }
        }
    }

    updatePlayerLists(jugadores) {
        // Actualizar lista de jugadores activos
        const activosList = document.querySelector('#jugadores-activos-list');
        if (activosList) {
            activosList.innerHTML = '';
            const jugadoresActivos = jugadores.filter(j => !j.eliminado);
            
            jugadoresActivos.forEach(jugador => {
                const li = document.createElement('li');
                li.className = 'list-group-item bg-dark text-light d-flex justify-content-between align-items-center';
                
                // Determinar si mostrar botones de host
                const hostControls = document.querySelector('.mt-4');
                const isHost = hostControls !== null; // Si existe el contenedor de controles del host
                
                let buttonsHtml = '';
                if (isHost) {
                    // Mostrar botones si es host (incluyendo para sí mismo)
                    const partidaData = this.getCurrentPartidaData();
                    
                    if (partidaData && partidaData.estado !== 'en_juego') {
                        // Si la partida no ha empezado, mostrar botón de expulsar
                        buttonsHtml = `
                            <button type="button" class="btn btn-sm btn-danger" onclick="partidaWS.expulsarJugador(${jugador.user_id})">
                                Expulsar
                            </button>
                        `;
                    } else if (partidaData && partidaData.estado === 'en_juego' && !partidaData.ronda_terminada) {
                        // Si la partida está en juego y la ronda no ha terminado, mostrar botón de eliminar
                        buttonsHtml = `
                            <button type="button" class="btn btn-sm btn-warning boton-juego" onclick="partidaWS.eliminarJugador(${jugador.id})">
                                Eliminar de ronda
                            </button>
                        `;
                    }
                }
                
                li.innerHTML = `
                    <span>
                        ${jugador.username}
                        ${jugador.es_host ? '<span class="badge bg-success ms-2">Host</span>' : ''}
                    </span>
                    ${buttonsHtml}
                `;
                activosList.appendChild(li);
            });
        }

        // Actualizar lista de jugadores eliminados
        const eliminadosList = document.querySelector('#jugadores-eliminados-list');
        if (eliminadosList) {
            eliminadosList.innerHTML = '';
            const jugadoresEliminados = jugadores.filter(j => j.eliminado);
            
            jugadoresEliminados.forEach(jugador => {
                const li = document.createElement('li');
                li.className = 'list-group-item bg-secondary text-light d-flex justify-content-between align-items-center';
                li.innerHTML = `
                    <span>
                        ${jugador.username}
                        ${jugador.es_host ? '<span class="badge bg-success ms-2">Host</span>' : ''}
                        ${jugador.es_impostor ? '<span class="badge bg-danger ms-2">Impostor</span>' : ''}
                        ${jugador.es_infiltrado ? '<span class="badge bg-warning ms-2">Infiltrado</span>' : ''}
                        ${jugador.es_bueno ? '<span class="badge bg-info ms-2">Bueno</span>' : ''}
                    </span>
                    <span class="badge bg-secondary">Eliminado</span>
                `;
                eliminadosList.appendChild(li);
            });
            
            // Mostrar u ocultar el contenedor de eliminados según si hay jugadores eliminados
            const eliminadosContainer = eliminadosList.closest('.col-md-6');
            if (eliminadosContainer) {
                if (jugadoresEliminados.length > 0) {
                    eliminadosContainer.style.display = 'block';
                } else {
                    eliminadosContainer.style.display = 'none';
                }
            }
        }
    }

    sendMessage(type, data = {}) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const message = {
                type: type,
                ...data
            };
            this.socket.send(JSON.stringify(message));
        }
    }

    eliminarJugador(jugadorId) {
        // Enviar mensaje al servidor
        this.sendMessage('eliminar_jugador', { jugador_id: jugadorId });
        
        // Mostrar notificación inmediata
        this.showNotification('Eliminando jugador...', 'info');
        
        // Solicitar actualización de datos después de un breve delay
        setTimeout(() => {
            this.requestRefresh();
        }, 500);
    }

    expulsarJugador(userId) {
        this.sendMessage('expulsar_jugador', { user_id: userId });
    }

    nuevaRonda() {
        this.sendMessage('nueva_ronda');
    }

    iniciarPartida() {
        this.sendMessage('iniciar_partida');
    }

    terminarPartida() {
        this.sendMessage('terminar_partida');
    }

    adivinarPalabra(palabra) {
        this.sendMessage('adivinar_palabra', { palabra_adivinada: palabra });
    }

    requestRefresh() {
        this.sendMessage('refresh_request');
        
        // Si no hay respuesta en 2 segundos, intentar de nuevo
        setTimeout(() => {
            if (this.socket && this.socket.readyState === WebSocket.OPEN) {
                this.sendMessage('refresh_request');
            }
        }, 2000);
    }

    showConnectionStatus(message, type) {
        // Crear o actualizar indicador de estado de conexión
        let statusElement = document.getElementById('connection-status');
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.id = 'connection-status';
            statusElement.className = 'alert alert-sm position-fixed top-0 end-0 m-3';
            statusElement.style.zIndex = '9999';
            document.body.appendChild(statusElement);
        }

        statusElement.className = `alert alert-${type} alert-sm position-fixed top-0 end-0 m-3`;
        statusElement.textContent = message;

        // Ocultar después de 3 segundos
        setTimeout(() => {
            if (statusElement.parentNode) {
                statusElement.parentNode.removeChild(statusElement);
            }
        }, 3000);
    }

    showNotification(message, type) {
        // Crear notificación toast
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        // Agregar al contenedor de toasts
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);

        // Mostrar el toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remover después de que se oculte
        toast.addEventListener('hidden.bs.toast', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }

    getCurrentPartidaData() {
        // Usar los datos almacenados del WebSocket si están disponibles
        if (this.currentPartidaData) {
            return this.currentPartidaData;
        }
        
        // Fallback: obtener datos actuales de la partida desde el DOM
        const estadoElement = document.querySelector('#estado-partida');
        const rondaTerminada = document.querySelector('.badge.bg-warning') !== null;
        
        if (estadoElement) {
            return {
                estado: estadoElement.textContent === 'En juego' ? 'en_juego' : 'esperando',
                ronda_terminada: rondaTerminada
            };
        }
        return null;
    }

    updatePalabraSecreta(palabraSecreta) {
        // Solo actualizar si la partida está en juego
        const estadoElement = document.querySelector('#estado-partida');
        if (estadoElement && estadoElement.textContent !== 'En juego') {
            return; // No actualizar si la partida no ha empezado
        }
        
        // Buscar el elemento que muestra la palabra secreta
        const palabraElement = document.querySelector('.alert-primary .display-6');
        if (palabraElement && palabraSecreta) {
            // Si es el mensaje del impostor, mostrarlo sin "Tu palabra secreta:"
            if (palabraSecreta.includes("¡Impostor!")) {
                palabraElement.innerHTML = `<b>${palabraSecreta}</b>`;
            } else {
                palabraElement.innerHTML = `Tu palabra secreta: <b>${palabraSecreta}</b>`;
            }
        }
    }

    // Esta función se eliminó porque estaba causando recargas innecesarias

    // Variable para almacenar los datos más recientes de la partida
    currentPartidaData = null;

    updatePartidaUI(partidaData) {
        // Guardar los datos actuales
        this.currentPartidaData = partidaData;
        
        // Actualizar tabla de puntuaciones
        this.updatePuntuacionTable(partidaData.jugadores);
        
        // Actualizar contadores de jugadores
        this.updatePlayerCounters(partidaData);
        
        // Actualizar estado de la partida
        this.updateGameState(partidaData);
        
        // Actualizar listas de jugadores activos y eliminados
        this.updatePlayerLists(partidaData.jugadores);
        
        // Actualizar palabra secreta del usuario actual
        this.updatePalabraSecreta(partidaData.palabra_secreta);
    }
} 