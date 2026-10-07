"""Mixin 1 of LoRABackend."""
from __future__ import annotations
from backend.core.observability.silent import swallow

from .part1 import (Any, FinetuneConfig, List, LoRAConfig, Path, inspect,)  # noqa: F401
class _Mixin1:
    def __init__(self) -> None:
        self._ok = self._check()

    @staticmethod
    def _check() -> bool:
        try:
            import torch  # noqa: F401
            import peft  # noqa: F401
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def available(self) -> bool:
        return self._ok

    def ready(self) -> bool:
        return self._ok

    def prepare(self, base_model: str, config: FinetuneConfig) -> Any:
        if not self._ok:
            raise RuntimeError(
                "torch/peft/transformers not installed: "
                "pip install torch peft transformers bitsandbytes"
            )
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        try:
            from transformers import BitsAndBytesConfig
        except ImportError:
            from transformers.utils.quantization_config import (
                BitsAndBytesConfig,
            )
        from peft import (
            LoraConfig, get_peft_model, prepare_model_for_kbit_training,
        )

        lora_cfg = config.lora or LoRAConfig()

        tokenizer = AutoTokenizer.from_pretrained(
            base_model, trust_remote_code=True,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        use_cuda = torch.cuda.is_available()
        bf16_ok = use_cuda and torch.cuda.is_bf16_supported()

        if use_cuda:
            bnb = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16 if bf16_ok else torch.float16,
                bnb_4bit_use_double_quant=True,
            )
            model = AutoModelForCausalLM.from_pretrained(
                base_model,
                quantization_config=bnb,
                device_map="auto",
                trust_remote_code=True,
            )
            model = prepare_model_for_kbit_training(model)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                base_model,
                torch_dtype=torch.float32,
                trust_remote_code=True,
            )

        try:
            model.config.use_cache = False
        except Exception as e:
            swallow("finetune.backends._peft_lora_parts.mixin1:79", e)

        peft_cfg = LoraConfig(
            r=lora_cfg.r,
            lora_alpha=lora_cfg.alpha,
            lora_dropout=lora_cfg.dropout,
            target_modules=list(lora_cfg.target_modules),
            bias=lora_cfg.bias,
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, peft_cfg)
        try:
            model.print_trainable_parameters()
        except Exception as e:
            swallow("finetune.backends._peft_lora_parts.mixin1:93", e)

        return {
            "base_model": base_model,
            "model": model,
            "tokenizer": tokenizer,
            "lora_config": peft_cfg,
            "config": config,
            "use_cuda": use_cuda,
            "bf16_ok": bf16_ok,
        }

    def train(self, artifact: Any, samples: List[Any], on_progress=None) -> Any:
        import torch  # noqa: F401
        from datasets import Dataset
        from transformers import (
            TrainingArguments, Trainer, DataCollatorForLanguageModeling,
        )
        from backend.finetune.data.formatter import format_chat

        if not isinstance(artifact, dict):
            raise TypeError("artifact must dict")

        model = artifact["model"]
        tokenizer = artifact["tokenizer"]
        config = artifact["config"]
        use_cuda = artifact["use_cuda"]
        bf16_ok = artifact["bf16_ok"]

        texts = [format_chat(s) for s in samples]
        ds = Dataset.from_dict({"text": texts})
        max_len = int(config.max_seq_len)

        def _tok(batch):
            # 只做 tokenize + truncate；labels 由 collator 从 input_ids 派生
            # padding 由 collator 在 batch 内动态处理（最长对齐）
            return tokenizer(
                batch["text"],
                truncation=True,
                max_length=max_len,
                padding=False,
            )

        ds = ds.map(_tok, batched=True, remove_columns=["text"])

        collator = DataCollatorForLanguageModeling(
            tokenizer=tokenizer, mlm=False,
        )

        output_dir = str(config.output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 按 TrainingArguments 真实签名过滤，兼容 transformers 4.x / 5.x
        valid = set(
            inspect.signature(TrainingArguments.__init__).parameters.keys()
        )

        kw: dict = dict(
            output_dir=output_dir,
            num_train_epochs=int(config.num_epochs),
            per_device_train_batch_size=int(config.batch_size),
            gradient_accumulation_steps=4,
            learning_rate=float(config.learning_rate),
            logging_steps=int(config.logging_steps),
            save_steps=int(config.save_steps),
            save_total_limit=2,
            bf16=bool(bf16_ok),
            fp16=bool(use_cuda and not bf16_ok),
            report_to=[],
            remove_unused_columns=False,
            optim="paged_adamw_8bit" if use_cuda else "adamw_torch",
        )
        # warmup: 优先 warmup_ratio，不支持则退化为 warmup_steps
        if "warmup_ratio" in valid:
            kw["warmup_ratio"] = float(config.warmup_ratio)
        elif "warmup_steps" in valid:
            total = max(1, int(config.num_epochs) * max(1, len(samples)))
            kw["warmup_steps"] = max(0, int(total * float(config.warmup_ratio)))

        kw = {k: v for k, v in kw.items() if k in valid}
        args = TrainingArguments(**kw)

        callbacks = []
        if on_progress is not None:
            from backend.finetune.backends.trainer_progress_callback import (
                ProgressCallback,
            )
            callbacks.append(ProgressCallback(on_progress))

        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=ds,
            data_collator=collator,
            callbacks=callbacks,
        )
        trainer.train()

        artifact["trained_model"] = model
        artifact["trainer"] = trainer
        return artifact
