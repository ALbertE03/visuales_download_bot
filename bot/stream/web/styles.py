

def styles()->str:
    return f"""<style>
            :root {{
                --primary: #6366f1;
                --primary-glow: rgba(99, 102, 241, 0.4);
                --bg-color: #030305;
                --panel-bg: rgba(20, 20, 25, 0.7);
                --panel-border: rgba(255, 255, 255, 0.06);
                --text-main: #ffffff;
                --text-muted: #a1a1aa;
            }}
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                background-color: var(--bg-color);
                background-image: 
                    radial-gradient(circle at 10% 0%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                    radial-gradient(circle at 90% 100%, rgba(168, 85, 247, 0.1) 0%, transparent 40%);
                background-attachment: fixed;
                font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
                color: var(--text-main);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 3rem 1.5rem;
                -webkit-font-smoothing: antialiased;
            }}
            .header {{
                width: 100%;
                max-width: 1200px;
                margin-bottom: 2.5rem;
                display: flex;
                align-items: center;
                gap: 14px;
            }}
            .brand-icon {{
                width: 42px;
                height: 42px;
                background: linear-gradient(135deg, #6366f1, #a855f7);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 8px 24px var(--primary-glow);
            }}
            .header-title {{
                font-size: 1.75rem;
                font-weight: 700;
                letter-spacing: -0.02em;
                background: linear-gradient(to right, #fff, #d4d4d8);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .player-card {{
                width: 100%;
                max-width: 1200px;
                background: var(--panel-bg);
                backdrop-filter: blur(24px);
                -webkit-backdrop-filter: blur(24px);
                border: 1px solid var(--panel-border);
                border-radius: 24px;
                overflow: hidden;
                box-shadow: 0 30px 60px -15px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.03);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .video-wrapper {{
                background: #000;
                width: 100%;
                aspect-ratio: 16/9;
                position: relative;
            }}
            .plyr {{
                height: 100%;
                --plyr-color-main: var(--primary);
                --plyr-video-background: transparent;
                --plyr-control-radius: 8px;
            }}
            .info-panel {{
                padding: 2rem 2.5rem;
            }}
            .title-group {{
                margin-bottom: 1.5rem;
            }}
            .filename {{
                font-size: 1.4rem;
                font-weight: 600;
                line-height: 1.4;
                color: #fff;
                margin-bottom: 0.8rem;
                word-break: break-word;
            }}
            .tags {{
                display: flex;
                gap: 0.75rem;
                align-items: center;
                flex-wrap: wrap;
            }}
            .badge {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.08);
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 0.85rem;
                font-weight: 500;
                color: var(--text-muted);
                letter-spacing: 0.01em;
            }}
            .badge-live {{
                background: rgba(99, 102, 241, 0.1);
                color: #818cf8;
                border-color: rgba(99, 102, 241, 0.2);
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .badge-live::before {{
                content: '';
                width: 6px;
                height: 6px;
                background: #818cf8;
                border-radius: 50%;
                box-shadow: 0 0 8px #818cf8;
            }}
            .controls-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 1rem;
                padding-top: 1.5rem;
                border-top: 1px solid var(--panel-border);
            }}
            .tools {{
                display: flex;
                gap: 0.75rem;
                flex-wrap: wrap;
            }}
            .btn {{
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 10px 20px;
                border-radius: 12px;
                font-size: 0.95rem;
                font-weight: 600;
                text-decoration: none;
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                cursor: pointer;
                border: none;
                user-select: none;
                outline: none;
            }}
            .btn-glow {{
                background: linear-gradient(135deg, var(--primary), #8b5cf6);
                color: white;
                box-shadow: 0 4px 15px var(--primary-glow), inset 0 1px 0 rgba(255,255,255,0.2);
            }}
            .btn-glow:hover {{
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(99, 102, 241, 0.6), inset 0 1px 0 rgba(255,255,255,0.2);
                filter: brightness(1.1);
            }}
            .btn-glow:active {{
                transform: translateY(0);
            }}
            .btn-glass {{
                background: rgba(255, 255, 255, 0.04);
                color: var(--text-main);
                border: 1px solid var(--panel-border);
            }}
            .btn-glass:hover {{
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.15);
                transform: translateY(-1px);
            }}
            .btn svg {{ width: 18px; height: 18px; }}
            
            input[type="file"] {{ display: none; }}
            
            select.btn-glass {{
                appearance: none;
                padding-right: 36px;
                background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='rgba(255,255,255,0.6)'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E");
                background-repeat: no-repeat;
                background-position: right 12px center;
                background-size: 16px;
                cursor: pointer;
            }}
            select.btn-glass:focus {{
                border-color: rgba(255,255,255,0.2);
                background-color: rgba(255,255,255,0.06);
            }}
            select option {{
                background: #18181b;
                color: #fff;
            }}
            
            @media (max-width: 768px) {{
                .info-panel {{ padding: 1.5rem; }}
                .filename {{ font-size: 1.25rem; }}
                body {{ padding: 1.5rem 1rem; }}
            }}
        </style>"""
