class Orchestrator:
    def __init__(self, analyser_collector, plan_writer, draft_writer, critic_agent, final_drafter):
        self.analyser_collector = analyser_collector
        self.plan_writer = plan_writer
        self.draft_writer = draft_writer
        self.critic_agent = critic_agent
        self.final_drafter = final_drafter

    def run(self, user_request):
        """
        Orchestration complète du processus d'écriture.
        Args:
            user_request (str): La demande de l'utilisateur.
        Returns:
            str: La version finale rédigée.
        """
        # 1. Trouver les articles pertinents
        articles_context = self.analyser_collector.process(user_request)
        
        # 2. Générer le plan détaillé
        plan = self.plan_writer.write_plan(user_request)
        
        # 3. Écrire le draft
        draft = self.draft_writer.write_draft(user_request, plan, articles_context)
        
        # 4. Critique du draft
        review = self.critic_agent.review_draft(draft)
        
        # 5. Réaliser la version finale
        final_version = self.final_drafter.finalize_draft(
            review.get("draft"),
            review.get("comments"),
            review.get("note")
        )
        
        return final_version
