"""
Script de diagnóstico para verificar la salida de WinGet
"""
import subprocess
import sys

def test_winget_output():
    """Prueba la salida de comandos winget para debug"""
    
    commands = [
        ['winget', 'list', '--source', 'winget', '--accept-source-agreements', '--disable-interactivity'],
        ['winget', 'upgrade', '--include-unknown', '--accept-source-agreements', '--disable-interactivity']
    ]
    
    for cmd in commands:
        print(f"\n{'='*80}")
        print(f"Ejecutando: {' '.join(cmd)}")
        print('='*80)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60,
                errors='replace'
            )
            
            print(f"\nReturn code: {result.returncode}")
            print(f"\nSTDOUT (primeros 1000 chars):")
            print("-" * 80)
            print(result.stdout[:1000])
            print("-" * 80)
            
            if result.stderr:
                print(f"\nSTDERR:")
                print("-" * 80)
                print(result.stderr[:500])
                print("-" * 80)
            
            # Buscar inicio de JSON
            json_start = result.stdout.find('{')
            if json_start != -1:
                print(f"\nJSON encontrado en posicion: {json_start}")
                print("Contenido antes del JSON:")
                print(repr(result.stdout[:json_start]))
            else:
                print("\n[!] NO se encontro JSON en la salida")

        except Exception as e:
            print(f"\n[X] Error: {e}")

if __name__ == "__main__":
    test_winget_output()
