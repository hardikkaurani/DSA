"""Web interface for Air Guitar control and monitoring."""
import logging
from flask import Flask, render_template, jsonify, request
from typing import Optional, Callable, Dict, Any
import threading

from utils.logger import setup_logger

logger = setup_logger(__name__)

class WebController:
    """Flask web interface for remote control and monitoring."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
        """
        Args:
            host: Flask server host
            port: Flask server port
            debug: Enable Flask debug mode
        """
        self.host = host
        self.port = port
        self.debug = debug
        
        self.app = Flask(__name__)
        self.app.config['JSON_SORT_KEYS'] = False
        
        # System state (shared with main app)
        self.system_state: Dict[str, Any] = {
            'recording': False,
            'active_voices': 0,
            'current_instrument': 'classic_guitar',
            'effects_enabled': False,
            'midi_enabled': False,
            'held_notes': [],
            'sensor_roll': 0.0,
            'sensor_force': 0
        }
        
        # Callbacks for control
        self.callbacks = {}
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard."""
            return render_template('index.html')
        
        @self.app.route('/api/state', methods=['GET'])
        def get_state():
            """Get current system state."""
            return jsonify(self.system_state)
        
        @self.app.route('/api/control/recording/start', methods=['POST'])
        def start_recording():
            """Start recording."""
            if 'on_start_recording' in self.callbacks:
                self.callbacks['on_start_recording']()
                return jsonify({'status': 'Recording started'})
            return jsonify({'error': 'Callback not registered'}), 400
        
        @self.app.route('/api/control/recording/stop', methods=['POST'])
        def stop_recording():
            """Stop recording."""
            if 'on_stop_recording' in self.callbacks:
                self.callbacks['on_stop_recording']()
                return jsonify({'status': 'Recording stopped'})
            return jsonify({'error': 'Callback not registered'}), 400
        
        @self.app.route('/api/control/instrument/<name>', methods=['POST'])
        def set_instrument(name: str):
            """Change instrument."""
            if 'on_instrument_change' in self.callbacks:
                self.callbacks['on_instrument_change'](name)
                return jsonify({'status': f'Instrument changed to {name}'})
            return jsonify({'error': 'Callback not registered'}), 400
        
        @self.app.route('/api/control/effects/<name>/<action>', methods=['POST'])
        def toggle_effect(name: str, action: str):
            """Toggle or configure effect."""
            enabled = action == 'enable'
            if 'on_effect_change' in self.callbacks:
                self.callbacks['on_effect_change'](name, enabled)
                return jsonify({'status': f'Effect {name} {action}d'})
            return jsonify({'error': 'Callback not registered'}), 400
        
        @self.app.route('/api/control/effect/<name>/param', methods=['POST'])
        def set_effect_param(name: str):
            """Set effect parameter."""
            data = request.get_json()
            param = data.get('param')
            value = data.get('value')
            
            if 'on_effect_param' in self.callbacks:
                self.callbacks['on_effect_param'](name, param, value)
                return jsonify({'status': f'Updated {name}.{param}'})
            return jsonify({'error': 'Callback not registered'}), 400
        
        @self.app.route('/api/control/midi/<action>', methods=['POST'])
        def toggle_midi(action: str):
            """Enable/disable MIDI."""
            enabled = action == 'enable'
            if 'on_midi_change' in self.callbacks:
                self.callbacks['on_midi_change'](enabled)
                return jsonify({'status': f'MIDI {action}d'})
            return jsonify({'error': 'Callback not registered'}), 400
        
        @self.app.route('/api/instruments', methods=['GET'])
        def list_instruments():
            """List available instruments."""
            # Dynamically load from instruction models
            try:
                from core.instrument_models import InstrumentFactory
                models = InstrumentFactory.list_models()
                return jsonify({'instruments': models})
            except:
                return jsonify({'error': 'Could not load instruments'}), 500
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
    
    def update_state(self, state_dict: Dict[str, Any]) -> None:
        """Update system state from main application."""
        self.system_state.update(state_dict)
    
    def register_callback(self, name: str, callback: Callable) -> None:
        """Register a callback for control actions."""
        self.callbacks[name] = callback
        logger.debug(f"Registered callback: {name}")
    
    def start(self) -> None:
        """Start Flask server in background thread."""
        thread = threading.Thread(
            target=lambda: self.app.run(host=self.host, port=self.port, debug=self.debug),
            daemon=True
        )
        thread.start()
        logger.info(f"Web controller started at http://{self.host}:{self.port}")
