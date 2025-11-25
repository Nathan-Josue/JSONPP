"""
Point d'entrée pour le visualiseur GUI standalone.
"""

import sys
import os

def main():
    """Point d'entrée principal."""
    try:
        # Vérifier que customtkinter est disponible
        import customtkinter  # noqa: F401
    except ImportError:
        print("❌ Erreur: customtkinter n'est pas installé", file=sys.stderr)
        print("   Installez-le avec: pip install customtkinter", file=sys.stderr)
        print("   Ou installez jsonplusplus avec le support GUI:", file=sys.stderr)
        print("   pip install jsonplusplus[gui]", file=sys.stderr)
        sys.exit(1)
    
    # Import après vérification
    from .viewer import main as viewer_main  # noqa: E402
    
    # Récupérer le fichier depuis les arguments de ligne de commande
    initial_file = None
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]
        if not os.path.exists(initial_file):
            print(f"❌ Erreur: Le fichier '{initial_file}' n'existe pas", file=sys.stderr)
            sys.exit(1)
    
    viewer_main(initial_file=initial_file)


if __name__ == "__main__":
    main()

