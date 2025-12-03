#!/usr/bin/env python3
"""
markov_gen.py
Simple Markov-chain text generator in pure Python (no external libraries).

Usage:
  1) Train a model and save it:
     python markov_gen.py train corpus.txt model.json --order 2

  2) Generate text from a saved model:
     python markov_gen.py gen model.json --length 100

  3) Quick: train & generate in one go:
     python markov_gen.py quick corpus.txt --order 2 --length 80

The model is stored as a JSON mapping from context -> {next_word:count}.
"""
import sys
import json
import random
import argparse
from collections import defaultdict
from typing import List, Tuple

def tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer (keeps punctuation attached for simplicity)."""
    # Very simple: split on whitespace. You can improve this with more rules if desired.
    return text.strip().split()

class MarkovChain:
    def __init__(self, order: int = 2):
        if order < 1:
            raise ValueError("order must be >= 1")
        self.order = order
        # mapping: context (tuple of words) -> dict(next_word -> count)
        self.model = defaultdict(lambda: defaultdict(int))

    def train(self, tokens: List[str]):
        """Train the model on a list of tokens (words)."""
        if len(tokens) < self.order:
            return
        # prepend START tokens and append STOP token to allow generation starts/ends
        START = "<START>"
        STOP = "<STOP>"
        padded = [START] * self.order + tokens + [STOP]
        for i in range(len(padded) - self.order):
            context = tuple(padded[i : i + self.order])
            next_word = padded[i + self.order]
            self.model[context][next_word] += 1

    def _choose_next(self, context: Tuple[str, ...]) -> str:
        """Choose next word based on counts for the given context."""
        choices = self.model.get(context)
        if not choices:
            # fallback: randomly choose from all known next words
            all_choices = []
            for nxts in self.model.values():
                all_choices.extend(nxts.keys())
            return random.choice(all_choices) if all_choices else "<STOP>"
        words, counts = zip(*choices.items())
        total = sum(counts)
        r = random.randrange(total)
        upto = 0
        for w, c in zip(words, counts):
            upto += c
            if r < upto:
                return w
        return words[-1]

    def generate(self, max_words: int = 100, start: List[str] = None) -> str:
        """Generate text up to max_words or until STOP token."""
        START = "<START>"
        STOP = "<STOP>"

        if start:
            # use provided start as initial context (may be shorter than order)
            tokens = start[:]
        else:
            tokens = []

        # build initial context
        if len(tokens) < self.order:
            context = tuple([START] * max(0, self.order - len(tokens)) + tokens[-self.order:])
        else:
            context = tuple(tokens[-self.order:])

        out = tokens[:]
        for _ in range(max_words):
            next_word = self._choose_next(context)
            if next_word == STOP:
                break
            out.append(next_word)
            context = tuple(list(context[1:]) + [next_word]) if self.order > 1 else (next_word,)
        return " ".join(out)

    def save(self, path: str):
        """Save model to JSON (converts tuple keys to strings)."""
        serial = {
            "order": self.order,
            "model": {
                "||".join(context): dict(nexts)
                for context, nexts in self.model.items()
            },
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serial, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        mc = cls(order=int(data.get("order", 2)))
        raw = data.get("model", {})
        for ctx_str, nexts in raw.items():
            context = tuple(ctx_str.split("||"))
            mc.model[context] = defaultdict(int, {k: int(v) for k, v in nexts.items()})
        return mc

def train_from_file(corpus_path: str, model_path: str, order: int = 2):
    with open(corpus_path, "r", encoding="utf-8") as f:
        text = f.read()
    tokens = tokenize(text)
    mc = MarkovChain(order=order)
    mc.train(tokens)
    mc.save(model_path)
    print(f"Trained model (order={order}) on {len(tokens)} tokens and saved to {model_path}")

def generate_from_model(model_path: str, length: int = 100, seed: int = None, start: List[str] = None):
    if seed is not None:
        random.seed(seed)
    mc = MarkovChain.load(model_path)
    text = mc.generate(max_words=length, start=start)
    print(text)
    return text

def quick_train_and_generate(corpus_path: str, order: int = 2, length: int = 80, seed: int = None):
    with open(corpus_path, "r", encoding="utf-8") as f:
        text = f.read()
    tokens = tokenize(text)
    mc = MarkovChain(order=order)
    mc.train(tokens)
    if seed is not None:
        random.seed(seed)
    out = mc.generate(max_words=length)
    print(out)
    return out

def main(argv):
    parser = argparse.ArgumentParser(description="Simple Markov chain text generator (no external libs).")
    sub = parser.add_subparsers(dest="cmd")

    p_train = sub.add_parser("train", help="Train model from corpus text file and save to JSON")
    p_train.add_argument("corpus", help="path to plain text corpus (UTF-8)")
    p_train.add_argument("model_out", help="output model json path")
    p_train.add_argument("--order", type=int, default=2, help="Markov order (1=unigram context, 2=bigram, etc.)")

    p_gen = sub.add_parser("gen", help="Generate text from a saved model JSON")
    p_gen.add_argument("model", help="path to model json")
    p_gen.add_argument("--length", type=int, default=100, help="max number of words to generate")
    p_gen.add_argument("--seed", type=int, default=None, help="random seed (optional)")

    p_quick = sub.add_parser("quick", help="Train on corpus and immediately generate (no model file saved)")
    p_quick.add_argument("corpus", help="path to corpus text")
    p_quick.add_argument("--order", type=int, default=2)
    p_quick.add_argument("--length", type=int, default=80)
    p_quick.add_argument("--seed", type=int, default=None)

    args = parser.parse_args(argv)

    if args.cmd == "train":
        train_from_file(args.corpus, args.model_out, order=args.order)
    elif args.cmd == "gen":
        generate_from_model(args.model, length=args.length, seed=args.seed)
    elif args.cmd == "quick":
        quick_train_and_generate(args.corpus, order=args.order, length=args.length, seed=args.seed)
    else:
        parser.print_help()

if __name__ == "__main__":
    main(sys.argv[1:])
