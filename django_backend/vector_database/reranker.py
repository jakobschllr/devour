"This Class defines a new reanking object to be used in Database objects to rerank query results"

from transformers import AutoModelForCausalLM, AutoTokenizer
from sentence_transformers import SentenceTransformer


class Reranker:
    def __init__(self, reranking_model : str, **kwargs):
        self.rank_model = AutoModelForCausalLM.from_pretrained(reranking_model).eval()
        self.rank_tokenizer = AutoTokenizer.from_pretrained(reranking_model)
        self.max_length = kwargs.get('max_length', 32768)
        self.task = "Given a document search query, retrieve relevant passages that answer the query"
        self.prefix = "<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\".<|im_end|>\n<|im_start|>user\n" \
                        if kwargs.get('prefix') is None else kwargs.get('prefix') 
        self.suffix = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n" if kwargs.get('suffix') is None else kwargs.get('suffix')
        

    def proces_inputs(self, pairs : list[str]):
        prefix_tokens = self.rank_tokenizer.encode(self.prefix, add_special_tokens=False)
        suffix_tokens = self.rank_tokenizer.encode(self.suffix, add_special_tokens=False)
        tokenised_pairs = self.rank_tokenizer(pairs, padding=False, truncation="longest_first", return_attention_mask=False, max_length=self.max_length-len(prefix_tokens) - len(suffix_tokens))
        return tokenised_pairs