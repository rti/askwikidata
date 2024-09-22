import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers


class LLM:
    def __init__(self, model_name="mistralai/Mistral-7B-Instruct-v0.1", device="cuda"):
        self.model_name = model_name
        self.device = device

        bnb_config = transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16,
            quantization_config=bnb_config,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.bos_token_id = 1
        self.stop_token_ids = [0]

    def __call__(self, prompt):
        encoded = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
        model_input = encoded
        model_input.to(self.device)
        generated_ids = self.model.generate(
            **model_input,
            do_sample=True,
            max_new_tokens=200,
            pad_token_id=self.tokenizer.eos_token_id
        )
        decoded = self.tokenizer.batch_decode(generated_ids)

        result = decoded[0]

        # mistrals response does not match prompt
        result = result.replace("<s> [INST]", "<s>[INST]") 

        # remove prompt from response
        result = result.replace(prompt, "")

        # remove end token
        result = result.replace("</s>", "")

        result = result.strip()

        return result
