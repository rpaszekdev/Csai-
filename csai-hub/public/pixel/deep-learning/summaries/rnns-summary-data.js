window.RNN_SUMMARY = {
  eyebrow: "CSAI@LIVE · DEEP LEARNING · L7 · RECURRENCE",
  title: "RNNS, LSTMS & GRUS",
  sub: "Visual exam summary — every section maps to a real lecturer-quiz question.",
  podcast: { href: "audio/rnns.mp3", label: "LISTEN · RNNS PODCAST" },
  source: "Source · Tilburg — Introduction to Deep Learning (800883-B-6)",
  sections: [
    {
      n: "01",
      title: "AN RNN IS A LOOP WITH MEMORY",
      exam: "Working principle: a loop feeds the hidden state h back in each step, so information persists across time.",
      figures: [
        { kind: "web", src: "https://upload.wikimedia.org/wikipedia/commons/b/b5/Recurrent_neural_network_unfold.svg", label: "WEB DIAGRAM", cap: "RNN unrolled through time", desc: "The same cell is copied at every step; the horizontal arrows carry the hidden state forward. That loop is the 'working principle' answer — information persists across the sequence." }
      ],
      ascii: `x1 → x2 → x3        (inputs over time)
 │     │     │
 ▼     ▼     ▼
[h1]→[h2]→[h3]       h = hidden state = running memory
 │     │     │
 ▼     ▼     ▼
 y1    y2    y3       (outputs)`
    },
    {
      n: "02",
      title: "THE ARCHITECTURE ZOO — MATCH THE SHAPE TO THE TASK",
      exam: "Translation, summarisation and parsing → ENCODER–DECODER (seq2seq).",
      figures: [
        { kind: "slide", slot: "rnn-s40", ph: "DROP slide-40", label: "LECTURE SLIDE", cap: "Encoder (many-to-one)", desc: "A whole input sequence is read; only the final hidden vector is kept as a summary. The 'many-to-one' shape — e.g. sentiment or author prediction." },
        { kind: "slide", slot: "rnn-s42", ph: "DROP slide-42", label: "LECTURE SLIDE", cap: "Decoder (one-to-many)", desc: "From one summary vector the network emits an output at every step — the 'one-to-many' shape, e.g. generating music from a single mood label." },
        { kind: "slide", slot: "rnn-s38", ph: "DROP slide-38", label: "LECTURE SLIDE", cap: "Encoder–decoder (seq2seq)", desc: "Encoder compresses the whole input, then the decoder generates the whole output. This is the shape tied to translation, summarisation and parsing." },
        { kind: "slide", slot: "rnn-s39", ph: "DROP slide-39", label: "LECTURE SLIDE", cap: "Seq2seq, unrolled", desc: "Same idea drawn step by step, so you can see where the encoder's summary hands over to the decoder." },
        { kind: "slide", slot: "rnn-s41", ph: "DROP slide-41", label: "LECTURE SLIDE", cap: "Seq2seq generation step", desc: "Each decoder step produces a token and passes its state on — how the output sequence is built one item at a time." }
      ],
      ascii: `one-to-many        many-to-one        many-to-many(sync)     encoder→decoder
  in                in in in            in in in              in in in ┊
   ↓                 ↓  ↓  ↓             ↓  ↓  ↓               ↘  ↓  ↙ ┊ ↓ ↓ ↓
 [h]→[h]→[h]        [h]→[h]→[h]         [h]→[h]→[h]           [h]→[h]→[h]┊[h]→[h]→[h]
  ↓   ↓   ↓               ↓             ↓   ↓   ↓                       ┊ ↓  ↓  ↓
 out out out             out           out out out                     ┊out out out
 (music from mood)  (sentiment/author) (tag each word)        (translate / summarise)`
    },
    {
      n: "03",
      title: "TRAINING: BPTT & THE VANISHING GRADIENT",
      exam: "BPTT gradients are w.r.t. the SHARED recurrent weights. Fix vanishing gradients with clipping, gating (LSTM/GRU) or attention — NOT dropout.",
      figures: [
        { kind: "slide", slot: "rnn-s03", ph: "DROP slide-03", label: "LECTURE SLIDE", cap: "Backpropagation Through Time", desc: "The loss gradient is propagated back along the unrolled chain. Exam point: these gradients are with respect to the shared recurrent weights, summed over every time step." },
        { kind: "slide", slot: "rnn-s04", ph: "DROP slide-04", label: "LECTURE SLIDE", cap: "Vanishing gradient", desc: "Multiplying small numbers at each step shrinks the gradient toward zero, so the earliest steps barely learn — the net can't link distant events." }
      ],
      ascii: `loss J
   ▲  multiply by small numbers at every hop ↓
[h1]←[h2]←[h3]← ... ←[hT]
  └─ gradient shrinks → ~0 ── early steps stop learning (the 'fading telephone game')`
    },
    {
      n: "04",
      title: "LSTM — THREE GATES",
      exam: "forget (drop old) · input (write new) · output (read out). Gates = SIGMOID; candidate = TANH.",
      figures: [
        { kind: "web", src: "https://upload.wikimedia.org/wikipedia/commons/1/17/The_LSTM_Cell.svg", label: "WEB DIAGRAM", cap: "LSTM cell", desc: "Three gates (forget, input, output) guard a protected cell state that runs straight through — giving gradients a clear highway. Gates are sigmoids; the candidate is a tanh." },
        { kind: "slide", slot: "rnn-s10", ph: "DROP slide-10", label: "LECTURE SLIDE", cap: "LSTM cell (lecture)", desc: "The lecturer's view of the same cell — the three gate units feeding the cell state." },
        { kind: "slide", slot: "rnn-s13", ph: "DROP slide-13", label: "LECTURE SLIDE", cap: "Output gate", desc: "The output gate decides how much of the cell state is read out as the hidden state passed to the next step." },
        { kind: "slide", slot: "rnn-s14", ph: "DROP slide-14", label: "LECTURE SLIDE", cap: "LSTM equations", desc: "Each gate f, i, o is a sigmoid of the inputs; the candidate uses tanh — confirming 'gates = sigmoid, candidate = tanh'." }
      ],
      ascii: `          ┌─ forget σ ─┐  drop irrelevant old memory
 C(t-1) ──┤             ├──► C(t)
          ├─ input  σ ─┤  write new (candidate = tanh)
 x,h ─────┤             │
          └─ output σ ─┘  → h(t) read out to next step`
    },
    {
      n: "05",
      title: "GRU — TWO GATES + THE CROSSFADE",
      exam: "reset r = how much past to use · update z = how much new replaces old.  h_t = (1−z)·h_(t-1) + z·h̃_t.",
      figures: [
        { kind: "web", src: "https://upload.wikimedia.org/wikipedia/commons/3/37/Gated_Recurrent_Unit%2C_base_type.svg", label: "WEB DIAGRAM", cap: "GRU cell", desc: "Only two gates — reset r and update z — and no separate cell state. Simpler than the LSTM, often just as good." },
        { kind: "slide", slot: "rnn-s20", ph: "DROP slide-20", label: "LECTURE SLIDE", cap: "GRU cell (lecture)", desc: "Shows the update gate z blending the previous hidden state with the new candidate." },
        { kind: "slide", slot: "rnn-s21", ph: "DROP slide-21", label: "LECTURE SLIDE", cap: "GRU equations", desc: "r and z are sigmoids; the candidate h-tilde uses the reset-gated previous state; the final state is the (1−z)/z blend." }
      ],
      ascii: `h_t = (1 − z) · h_(t-1)   +   z · h̃_t
          └─ keep OLD ─┘        └─ take NEW ─┘

 z ≈ 0 :  ██████████░░░░   mostly OLD memory  (smooth carry-over → beats vanishing gradient)
 z ≈ 1 :  ░░░░███████████   mostly NEW candidate
 reset r ≈ 0 : ignore the past entirely (e.g. a fresh sentence)`
    },
    {
      n: "06",
      title: "SEQ2SEQ & THE CHOICES THE EXAM QUIETLY TESTS",
      exam: "Pick the last layer + loss by the task. Teacher forcing feeds the real previous token during training.",
      figures: [
        { kind: "slide", slot: "rnn-s22", ph: "DROP slide-22", label: "LECTURE SLIDE", cap: "Seq2Seq", desc: "The encoder turns the input into a context vector; the decoder unrolls that into the output sequence." },
        { kind: "slide", slot: "rnn-s24", ph: "DROP slide-24", label: "LECTURE SLIDE", cap: "Toward embeddings", desc: "Bridges sequence models to embeddings — how tokens become the vectors an RNN consumes." }
      ],
      table: {
        head: ["Task", "Last layer", "Loss"],
        rows: [
          ["Binary (e.g. urgent email?)", "1 node · sigmoid", "Binary cross-entropy"],
          ["Multi-class (42 car brands)", "42 nodes · softmax", "Categorical cross-entropy"],
          ["Regression (predict a score)", "linear", "MSE"],
          ["Hidden layers", "tanh (bounds activations)", "—"]
        ]
      }
    }
  ]
};
