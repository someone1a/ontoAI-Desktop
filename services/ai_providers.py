from abc import ABC, abstractmethod
from typing import Optional


class AIProvider(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

    @abstractmethod
    def test_connection(self) -> tuple[bool, str]:
        pass


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model

    def generate_response(self, prompt: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en coaching profesional."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error al conectar con OpenAI: {str(e)}"

    def test_connection(self) -> tuple[bool, str]:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )

            return True, f"Conexión exitosa con modelo {self.model}"
        except Exception as e:
            return False, f"Error: {str(e)}"


class GroqCloudProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.model = model

    def generate_response(self, prompt: str) -> str:
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente experto en coaching profesional."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Error al conectar con GroqCloud: {str(e)}"

    def test_connection(self) -> tuple[bool, str]:
        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=10
            )

            return True, f"Conexión exitosa con modelo {self.model}"
        except Exception as e:
            return False, f"Error: {str(e)}"


class GPT4AllProvider(AIProvider):
    def __init__(self, model_path: str):
        self.model_path = model_path

    def generate_response(self, prompt: str) -> str:
        try:
            from gpt4all import GPT4All
            model = GPT4All(self.model_path)

            system_prompt = "Eres un asistente experto en coaching profesional."
            full_prompt = f"{system_prompt}\n\nUsuario: {prompt}\n\nAsistente:"

            response = model.generate(full_prompt, max_tokens=1000)
            return response
        except Exception as e:
            return f"Error al conectar con GPT4All: {str(e)}"

    def test_connection(self) -> tuple[bool, str]:
        try:
            from gpt4all import GPT4All
            model = GPT4All(self.model_path)
            response = model.generate("Test", max_tokens=10)
            return True, f"Modelo local cargado correctamente"
        except Exception as e:
            return False, f"Error: {str(e)}"


class MixtralProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "mixtral-8x7b-32768"):
        self.groq_provider = GroqCloudProvider(api_key, model)

    def generate_response(self, prompt: str) -> str:
        return self.groq_provider.generate_response(prompt)

    def test_connection(self) -> tuple[bool, str]:
        return self.groq_provider.test_connection()


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model

    def generate_response(self, prompt: str) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            model = genai.GenerativeModel(self.model)

            system_instruction = "Eres un asistente experto en coaching profesional."
            full_prompt = f"{system_instruction}\n\n{prompt}"

            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Error al conectar con Gemini: {str(e)}"

    def test_connection(self) -> tuple[bool, str]:
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            model = genai.GenerativeModel(self.model)
            response = model.generate_content("Test")

            return True, f"Conexión exitosa con modelo {self.model}"
        except Exception as e:
            return False, f"Error: {str(e)}"


class AIProviderFactory:
    @staticmethod
    def create_provider(provider_name: str, config: dict) -> Optional[AIProvider]:
        if provider_name == "OpenAI":
            return OpenAIProvider(
                api_key=config.get('api_key', ''),
                model=config.get('model', 'gpt-4')
            )
        elif provider_name == "GroqCloud":
            return GroqCloudProvider(
                api_key=config.get('api_key', ''),
                model=config.get('model', 'mixtral-8x7b-32768')
            )
        elif provider_name == "GPT4All":
            return GPT4AllProvider(
                model_path=config.get('model_path', '')
            )
        elif provider_name == "Mixtral":
            return MixtralProvider(
                api_key=config.get('api_key', ''),
                model=config.get('model', 'mixtral-8x7b-32768')
            )
        elif provider_name == "Gemini":
            return GeminiProvider(
                api_key=config.get('api_key', ''),
                model=config.get('model', 'gemini-pro')
            )
        return None
