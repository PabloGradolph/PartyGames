class PartidaWebSocket {
    constructor(codigoPartida) {
        this.codigoPartida = codigoPartida;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.currentPartidaData = null;
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
            this.reconnectAttempts = 0;
            this.initializePartidaData();
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('Error al parsear mensaje WebSocket:', error);
            }
        };

        this.socket.onclose = (event) => {
            
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
                // Forzar recarga si el número de eliminados aumenta
                if (this.currentPartidaData && data.data.jugadores_eliminados > this.currentPartidaData.jugadores_eliminados) {
                    this.showNotification('Un jugador ha sido eliminado', 'danger');
                    setTimeout(() => window.location.reload(), 1000);
                    return;
                }
                
                // También detectar si hay cambios en la lista de jugadores
                if (this.currentPartidaData && this.currentPartidaData.jugadores) {
                    const jugadoresActuales = this.currentPartidaData.jugadores;
                    const jugadoresNuevos = data.data.jugadores;
                    
                    const cambiosDetectados = jugadoresActuales.some((jugadorActual, index) => {
                        const jugadorNuevo = jugadoresNuevos[index];
                        return jugadorActual.eliminado !== jugadorNuevo.eliminado;
                    });
                    
                    if (cambiosDetectados) {
                        this.showNotification('Un jugador ha sido eliminado', 'danger');
                        setTimeout(() => window.location.reload(), 1000);
                        return;
                    }
                    
                    // Detectar si un impostor eliminado intentó adivinar (cambios en puntos o estado)
                    const cambiosImpostor = jugadoresActuales.some((jugadorActual, index) => {
                        const jugadorNuevo = jugadoresNuevos[index];
                        // Si es un impostor eliminado y sus puntos cambiaron, probablemente intentó adivinar
                        if (jugadorActual.es_impostor && jugadorActual.eliminado && 
                            jugadorNuevo.es_impostor && jugadorNuevo.eliminado &&
                            jugadorActual.puntos !== jugadorNuevo.puntos) {
                            return true;
                        }
                        return false;
                    });
                    
                    if (cambiosImpostor) {
                        this.showNotification('Un impostor eliminado intentó adivinar la palabra', 'info');
                        setTimeout(() => window.location.reload(), 1000);
                        return;
                    }
                }
                
                this.currentPartidaData = data.data;
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
                setTimeout(() => window.location.reload(), 1000);
                break;
                
            case 'jugador_expulsado':
                this.showNotification('Un jugador ha sido expulsado de la partida', 'warning');
                setTimeout(() => window.location.reload(), 1000);
                break;
                
            case 'partida_iniciada':
                this.showNotification(data.message, 'success');
                setTimeout(() => window.location.reload(), 1000);
                setTimeout(() => window.location.reload(), 3000);
                break;
                
            case 'nueva_ronda_iniciada':
                this.showNotification(data.message, 'success');
                setTimeout(() => window.location.reload(), 1000);
                setTimeout(() => window.location.reload(), 3000);
                break;
                
            case 'partida_terminada':
                this.showNotification(data.message, 'warning');
                setTimeout(() => {
                    window.location.href = '/';
                }, 3000);
                break;
                
            case 'error':
                this.showNotification(data.message, 'danger');
                break;
                
            case 'ronda_terminada':
                this.showNotification(data.message, 'warning');
                setTimeout(() => window.location.reload(), 2000);
                break;
                
            case 'adivinacion_resultado':
                if (data.resultado.error) {
                    this.showNotification(data.resultado.error, 'danger');
                } else {
                    this.showNotification(data.resultado.mensaje, data.resultado.correcto ? 'success' : 'warning');
                    // Recargar la página después de mostrar el resultado de la adivinación
                    setTimeout(() => window.location.reload(), 2000);
                }
                break;
        }
    }

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
        const estadoElement = document.querySelector('#estado-partida');
        if (estadoElement) {
            estadoElement.textContent = partidaData.estado === 'en_juego' ? 'En juego' : 'Esperando';
        }

        const puntuacionRow = document.querySelector('.row.mb-4');
        if (puntuacionRow) {
            puntuacionRow.style.display = partidaData.estado === 'en_juego' ? 'block' : 'none';
        }

        const botonesJuego = document.querySelectorAll('.boton-juego');
        botonesJuego.forEach(boton => {
            boton.style.display = partidaData.estado === 'en_juego' ? 'inline-block' : 'none';
        });

        this.updateStartButton(partidaData);
    }

    updateStartButton(partidaData) {
        const hostControls = document.querySelector('.mt-4');
        if (!hostControls) return;

        let startButton = hostControls.querySelector('#start-game-button');
        let warningDiv = hostControls.querySelector('#warning-message');

        const oldButtons = hostControls.querySelectorAll('button[onclick*="iniciarPartida"]');
        const oldWarnings = hostControls.querySelectorAll('.alert-warning');
        
        oldButtons.forEach(btn => {
            if (!btn.id) btn.remove();
        });
        oldWarnings.forEach(warn => {
            if (!warn.id) warn.remove();
        });

        if (partidaData.jugadores_activos >= 4 && partidaData.estado !== 'en_juego') {
            if (warningDiv) {
                warningDiv.style.display = 'none';
            }
            
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
            if (startButton) {
                startButton.style.display = 'none';
            }
            
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
            if (startButton) {
                startButton.style.display = 'none';
            }
            if (warningDiv) {
                warningDiv.style.display = 'none';
            }
        }
    }

    updatePlayerLists(jugadores) {
        const activosList = document.querySelector('#jugadores-activos-list');
        if (activosList) {
            activosList.innerHTML = '';
            const jugadoresActivos = jugadores.filter(j => !j.eliminado);
            
            jugadoresActivos.forEach(jugador => {
                const li = document.createElement('li');
                li.className = 'list-group-item bg-dark text-light d-flex justify-content-between align-items-center';
                
                const hostControls = document.querySelector('.mt-4');
                const isHost = hostControls !== null;
                
                let buttonsHtml = '';
                if (isHost) {
                    const partidaData = this.getCurrentPartidaData();
                    
                    if (partidaData && partidaData.estado !== 'en_juego') {
                        buttonsHtml = `
                            <button type="button" class="btn btn-sm btn-danger" onclick="partidaWS.expulsarJugador(${jugador.user_id})">
                                Expulsar
                            </button>
                        `;
                    } else if (partidaData && partidaData.estado === 'en_juego' && !partidaData.ronda_terminada) {
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

        let eliminadosList = document.querySelector('#jugadores-eliminados-list');
        const jugadoresEliminados = jugadores.filter(j => j.eliminado);
        
        let eliminadosContainer = eliminadosList ? eliminadosList.closest('.col-md-6') : null;
        if (!eliminadosContainer) {
            const row = document.querySelector('.row');
            if (row) {
                eliminadosContainer = document.createElement('div');
                eliminadosContainer.className = 'col-md-6';
                eliminadosContainer.innerHTML = `
                    <h4>Eliminados de la ronda (<span id="jugadores-eliminados-count">${jugadoresEliminados.length}</span>)</h4>
                    <ul id="jugadores-eliminados-list" class="list-group list-group-flush mb-3">
                    </ul>
                `;
                row.appendChild(eliminadosContainer);
                eliminadosList = eliminadosContainer.querySelector('#jugadores-eliminados-list');
            }
        }
        
        if (eliminadosList) {
            eliminadosList.innerHTML = '';
            
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
            
            const countElement = document.querySelector('#jugadores-eliminados-count');
            if (countElement) {
                countElement.textContent = jugadoresEliminados.length;
            }
            
            if (eliminadosContainer) {
                eliminadosContainer.style.display = jugadoresEliminados.length > 0 ? 'block' : 'none';
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
        this.sendMessage('eliminar_jugador', { jugador_id: jugadorId });
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

    showConnectionStatus(message, type) {
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

        setTimeout(() => {
            if (statusElement.parentNode) {
                statusElement.parentNode.removeChild(statusElement);
            }
        }, 3000);
    }

    showNotification(message, type) {
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

        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

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
        if (this.currentPartidaData) {
            return this.currentPartidaData;
        }
        
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

    initializePartidaData() {
        const activosCount = document.querySelector('#jugadores-activos-count');
        const eliminadosCount = document.querySelector('#jugadores-eliminados-count');
        const estadoElement = document.querySelector('#estado-partida');
        
        this.currentPartidaData = {
            jugadores_activos: activosCount ? parseInt(activosCount.textContent) : 0,
            jugadores_eliminados: eliminadosCount ? parseInt(eliminadosCount.textContent) : 0,
            estado: estadoElement ? (estadoElement.textContent === 'En juego' ? 'en_juego' : 'esperando') : 'esperando',
            ronda_terminada: document.querySelector('.badge.bg-warning') !== null
        };
        
        if (this.currentPartidaData.estado === 'en_juego') {
            setTimeout(() => window.location.reload(), 2000);
        }
    }

    updatePalabraSecreta(palabraSecreta) {
        const estadoElement = document.querySelector('#estado-partida');
        if (estadoElement && estadoElement.textContent !== 'En juego') {
            return;
        }
        
        const palabraElement = document.querySelector('.alert-primary .display-6');
        if (palabraElement && palabraSecreta) {
            if (palabraSecreta.includes("¡Impostor!")) {
                palabraElement.innerHTML = `<b>${palabraSecreta}</b>`;
            } else {
                palabraElement.innerHTML = `Tu palabra secreta: <b>${palabraSecreta}</b>`;
            }
        }
    }

    updatePartidaUI(partidaData) {
        this.currentPartidaData = partidaData;
        this.updatePuntuacionTable(partidaData.jugadores);
        this.updatePlayerCounters(partidaData);
        this.updateGameState(partidaData);
        this.updatePlayerLists(partidaData.jugadores);
        this.updatePalabraSecreta(partidaData.palabra_secreta);
    }
} 