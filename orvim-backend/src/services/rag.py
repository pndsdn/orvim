def generate_response(
        question: str,
        model_name: str,
        db_id: str,
        n_results: int,
        use_additional_instruction: bool = True,
        additional_instruction: str = "после вашего ответа укажите самые релевантные номера документов, которые вы использовали для ответа, в формате: <documents_start>[номера документов через запятую] <documents_end>",
        prompt_template: str = None,
        llm_name: str = "OpenAI",
        llm_kwargs: dict = None,
        **kwargs) -> str:
    pass
