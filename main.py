from pathlib import Path
from agents.analyser_collector import AnalyserCollector
from agents.vector_db_client import VectorDBClient
from agents.plan_writer import PlanWriter
from agents.draft_writer import DraftWriter
from agents.final_drafter import FinalDrafter
from agents.orchestrator import Orchestrator

# TODO: Ajouter l'import ou l'implémentation de CriticAgent lorsque disponible.

def main():
    # Chemins vers les fichiers de la base vectorielle
    ROOT = Path(__file__).parent
    EMBEDDINGS_PATH = ROOT / "data" / "vectors_base" / "embeddings.npy"
    METADATA_PATH = ROOT / "data" / "vectors_base" / "metadata.jsonl"
    
    # Initialisation du client de base vectorielle
    RAW_DIR = ROOT / "data" / "raw"
    try:
        vector_db_client = VectorDBClient(
            embeddings_path=str(EMBEDDINGS_PATH),
            metadata_path=str(METADATA_PATH),
            raw_dir=str(RAW_DIR) if RAW_DIR.exists() else None
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure that embeddings.npy and metadata.jsonl exist in data/vectors_base/")
        return
    
    # Initialisation des sous-composants
    analyser_collector = AnalyserCollector(vector_db_client, top_k=10, similarity_threshold=0.3)
    plan_writer = PlanWriter()
    draft_writer = DraftWriter()
    final_drafter = FinalDrafter()
    critic_agent = None  # TODO: Instancier l'agent critique réel

    orchestrator = Orchestrator(
        analyser_collector=analyser_collector,
        plan_writer=plan_writer,
        draft_writer=draft_writer,
        critic_agent=critic_agent,
        final_drafter=final_drafter
    )

    user_request = input("Entrez votre demande : ")
    final_output = orchestrator.run(user_request)
    print("Version finale générée :\n", final_output)

if __name__ == "__main__":
    main()