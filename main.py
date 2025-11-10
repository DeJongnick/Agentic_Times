from agents.analyser_collector import AnalyserCollector
from agents.plan_writer import PlanWriter
from agents.draft_writer import DraftWriter
from agents.final_drafter import FinalDrafter
from agents.orchestrator import Orchestrator

# TODO: Ajouter l'import ou l'implémentation de CriticAgent lorsque disponible.

def main():
    # Initialisation des sous-composants (passer les dépendances/clients nécessaires)
    vector_db_client = None  # TODO: initialiser avec le client de la base vectorielle réelle
    analyser_collector = AnalyserCollector(vector_db_client)
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