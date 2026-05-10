
def scripts()->str:
    return f"""<script src="https://cdn.plyr.io/3.7.8/plyr.polyfilled.js"></script>
        <script>
            document.addEventListener('DOMContentLoaded', () => {{
                const video = document.getElementById('player');
                const player = new Plyr(video, {{
                    captions: {{ active: true, update: true, language: 'auto' }},
                    fullscreen: {{
                        enabled: true,
                        fallback: true,
                        iosNative: true,
                        container: null
                    }},
                    i18n: {{
                        quality: 'Calidad',
                        speed: 'Velocidad',
                        captions: 'Subtítulos',
                        disabled: 'Desactivado',
                        enabled: 'Activado',
                    }}
                }});

                document.getElementById('sub-upload').addEventListener('change', function(e) {{
                    const file = e.target.files[0];
                    if (!file) return;

                    const url = URL.createObjectURL(file);
                    const track = document.createElement('track');
                    track.kind = 'captions';
                    track.label = file.name;
                    track.srclang = 'es';
                    track.src = url;
                    track.default = true;

                    Array.from(video.querySelectorAll('track')).forEach(t => t.remove());
                    video.appendChild(track);
                    
                    // Animación de éxito
                    const label = this.parentElement;
                    const originalText = label.innerHTML;
                    label.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Cargado con éxito`;
                    label.style.borderColor = '#4ade80';
                    label.style.color = '#4ade80';
                    
                    setTimeout(() => {{
                        track.mode = 'showing';
                        setTimeout(() => {{
                            label.innerHTML = originalText;
                            label.style.borderColor = '';
                            label.style.color = '';
                        }}, 3000);
                    }}, 500);
                }});

                video.addEventListener('loadedmetadata', () => {{
                    const audioTracks = video.audioTracks;
                    const selector = document.getElementById('audio-track-selector');
                    if (audioTracks && audioTracks.length > 1) {{
                        selector.style.display = 'inline-flex';
                        selector.innerHTML = '';
                        for (let i = 0; i < audioTracks.length; i++) {{
                            const option = document.createElement('option');
                            option.value = i;
                            option.text = audioTracks[i].label || audioTracks[i].language || `Audio Track ${{i + 1}}`;
                            selector.appendChild(option);
                            
                            if (audioTracks[i].enabled) {{
                                option.selected = true;
                            }}
                        }}
                        
                        selector.addEventListener('change', (e) => {{
                            for (let i = 0; i < audioTracks.length; i++) {{
                                audioTracks[i].enabled = (i == parseInt(e.target.value));
                            }}
                        }});
                    }}
                }});
            }});
        </script>"""
