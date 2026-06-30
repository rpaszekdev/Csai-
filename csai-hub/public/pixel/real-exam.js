// Real Introduction-to-Deep-Learning exam (800883-B-6), transcribed from the
// 20 exam screenshots in Real-Exam-Questions/. Pushed onto window.DL_LESSONS so
// the pixel quiz engine renders it as a "REAL" tab — no engine changes.
//
// Answer keys are TUTOR-DERIVED, not official: the source screenshots are review
// shots showing the student's own (often wrong) answers, which are NOT a key.
// Matching / ordering / numeric questions are expressed with the engine's
// existing dropdown blanks (code:true preserves the line layout).
(function () {
  const questions = [
    // Q1 — decoder attention (matching, 9 rows)
    {
      n: 1, type: "dropdown", code: true,
      q: "A student claims every attention layer in a translation Transformer's decoder does the same job. Match each description (a–i) to the best interpretation.\n\nLEGEND  1 = decoder MASKED self-attention   2 = WRONG: confuses masking with access to future tokens   3 = WRONG: overstates attention's role in representing word order   4 = decoder CROSS-attention\n\na) Q, K and V are all derived from decoder-side reps in the same sublayer   [[1]]\nb) \"needed so the decoder can look AHEAD at future target tokens during training\"   [[2]]\nc) combines earlier generated target positions while blocking access to future tokens   [[3]]\nd) replacing it with encoder-only attention would lose direct target-side context   [[4]]\ne) conditions the next prediction on source reps produced by the encoder   [[5]]\nf) \"the ONLY reason the decoder can represent target-side word order\"   [[6]]\ng) removing it prevents aligning target decisions with relevant source content   [[7]]\nh) Q comes from the decoder; K and V come from encoder outputs   [[8]]\ni) selectively retrieves information from the encoded source sentence   [[9]]",
      blanks: [
        { label: "a", pool: ["1", "2", "3", "4"], correct: "1" },
        { label: "b", pool: ["1", "2", "3", "4"], correct: "2" },
        { label: "c", pool: ["1", "2", "3", "4"], correct: "1" },
        { label: "d", pool: ["1", "2", "3", "4"], correct: "1" },
        { label: "e", pool: ["1", "2", "3", "4"], correct: "4" },
        { label: "f", pool: ["1", "2", "3", "4"], correct: "3" },
        { label: "g", pool: ["1", "2", "3", "4"], correct: "4" },
        { label: "h", pool: ["1", "2", "3", "4"], correct: "4" },
        { label: "i", pool: ["1", "2", "3", "4"], correct: "4" },
      ],
      explain: "Masked self-attention (1) = Q/K/V all decoder-side, looks only at already-generated tokens (a,c,d). Cross-attention (4) = Q from decoder, K/V from encoder, pulls in source content (e,g,h,i). (b) is the classic masking misconception; (f) overstates attention vs positional encodings for word order. Tutor-derived key.",
    },
    // Q2 — CNN concepts (matching, some have no match)
    {
      n: 2, type: "dropdown", code: true,
      q: "Match each description (1–9) to the best concept. Some descriptions have NO correct match.\n\nCONCEPTS  filter = convolutional filter · lowfeat = low-level feature extraction · cnn = CNN · mlp = MLP · share = weight sharing · fmap = feature map · none = no match\n\n1) main purpose of convolution is to turn a 2D image into a 1D vector before classification   [[1]]\n2) main role of convolution in early hidden layers   [[2]]\n3) learned component that responds to local patterns such as vertical edges   [[3]]\n4) guarantees a CNN recognises an object regardless of its orientation   [[4]]\n5) architecture that does NOT preserve 2D neighbourhood structure after flattening   [[5]]\n6) representation storing the final class probabilities (cat / dog / car)   [[6]]\n7) reduces parameters by reusing one detector across the image   [[7]]\n8) model family for spatially structured inputs, based on a translation-equivariant op   [[8]]\n9) response of a learned detector at different spatial positions   [[9]]",
      blanks: [
        { label: "1", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "none" },
        { label: "2", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "lowfeat" },
        { label: "3", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "filter" },
        { label: "4", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "none" },
        { label: "5", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "mlp" },
        { label: "6", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "none" },
        { label: "7", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "share" },
        { label: "8", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "cnn" },
        { label: "9", pool: ["filter", "lowfeat", "cnn", "mlp", "share", "fmap", "none"], correct: "fmap" },
      ],
      explain: "1 (flatten), 4 (rotation invariance) and 6 (class probabilities = softmax output, not a listed concept) have no match. CNNs are translation-equivariant, not rotation-invariant. Tutor-derived key.",
    },
    // Q3 — RNN vs Transformer efficiency (single)
    {
      n: 3, type: "single",
      q: "An RNN and a Transformer are trained on the same task. For short sequences the Transformer is faster; once sequences get long enough, the Transformer becomes LESS efficient than the RNN. Which explanation is best?",
      options: {
        A: "The RNN is more efficient for long sequences because backprop-through-time is cheaper than backprop in self-attention, regardless of model size.",
        B: "The Transformer is mainly efficient for short sequences because it emphasises local context, whereas the RNN gains efficiency once longer dependencies dominate.",
        C: "The RNN becomes faster for long sequences because recurrent connections let all time steps be processed in parallel, while the Transformer processes tokens one by one.",
        D: "The Transformer parallelises across positions (fast on short sequences), but self-attention cost grows quadratically with sequence length, unlike the more gradual scaling of recurrent updates.",
      },
      correct: "D",
      explain: "Self-attention is O(n²) in sequence length; the RNN is O(n) per layer. So the Transformer's parallelism wins on short n but loses once n is large. C is backwards (RNNs are sequential, not parallel).",
    },
    // Q4 — segmentation claims (multi: select all INCORRECT)
    {
      n: 4, type: "multi",
      q: "A paper proposes a convolutional encoder–decoder for semantic segmentation (a class label per pixel). Select ALL reviewer comments that are conceptually INCORRECT.",
      options: {
        A: "Using upsampling is consistent with recovering higher-resolution prediction maps in later layers.",
        B: "It is correct to describe segmentation as predicting a class label for each pixel.",
        C: "Preserving spatial structure is mistaken, because the purpose of convolution is to remove spatial information and treat each pixel independently.",
        D: "Describing convolution as extracting local visual patterns is appropriate for segmentation.",
        E: "Pooling / downsampling is always incompatible with segmentation, because any resolution reduction permanently prevents pixel-level prediction.",
        F: "The network should avoid changing the number of channels across layers, because pixelwise classification requires the channel dimension to stay constant.",
        G: "Representing the output with one channel per class at each spatial location is reasonable for multi-class segmentation.",
        H: "The final feature map should be flattened into a 1-D vector before classification, because that preserves pixel-level correspondences.",
        I: "Skip connections are justified because early layers carry fine spatial detail useful to later prediction layers.",
      },
      correct: ["C", "E", "F", "H"],
      explain: "C (convolution keeps spatial structure), E (\"always\" — encoder–decoder recovers resolution), F (channels change freely; final channels = #classes) and H (flattening destroys spatial correspondence) are wrong. A,B,D,G,I are correct. The student missed F. Tutor-derived key.",
    },
    // Q5 — GRU update ordering
    {
      n: 5, type: "dropdown", code: true,
      q: "Arrange the computations of ONE GRU update in the order they are performed.\n\nSTEPS  gates = compute reset & update gates from x_t and h_(t-1) · reset = reset gate filters h_(t-1) for the candidate · cand = compute candidate hidden state · update = update gate blends h_(t-1) and candidate into h_t\n\nFirst:   [[1]]\nSecond:  [[2]]\nThird:   [[3]]\nFourth:  [[4]]",
      blanks: [
        { label: "1st", pool: ["gates", "reset", "cand", "update"], correct: "gates" },
        { label: "2nd", pool: ["gates", "reset", "cand", "update"], correct: "reset" },
        { label: "3rd", pool: ["gates", "reset", "cand", "update"], correct: "cand" },
        { label: "4th", pool: ["gates", "reset", "cand", "update"], correct: "update" },
      ],
      explain: "Gates first (need r, z), then r filters h_(t-1), then the candidate h̃ is formed, finally z blends h_(t-1) and h̃ into the new state.",
    },
    // Q6 — normalization cloze (inline dropdown)
    {
      n: 6, type: "dropdown",
      q: "Normalization methods differ in which values are normalized together. [[1]] uses statistics across the examples in a mini-batch, so its behaviour depends on the size and composition of the [[2]]. In contrast, [[3]] computes statistics independently for each sample, across that sample's features. Such per-sample methods normalize across a vector of [[4]] within one example. [[5]] normalizes channels in groups. Batch norm performs poorly with very small mini-batches because the estimated statistics become [[6]]. [[7]] normalizes each channel independently per sample, whereas [[8]] is the method that relies on sufficiently large mini-batches.",
      blanks: [
        { label: "1", pool: ["Batch normalization", "Layer normalization", "Instance normalization", "Group normalization"], correct: "Batch normalization" },
        { label: "2", pool: ["mini-batch", "layer", "feature", "channel"], correct: "mini-batch" },
        { label: "3", pool: ["Batch normalization", "Layer normalization", "Instance normalization", "Group normalization"], correct: "Layer normalization" },
        { label: "4", pool: ["features", "examples", "batches", "gradients"], correct: "features" },
        { label: "5", pool: ["Batch normalization", "Layer normalization", "Instance normalization", "Group normalization"], correct: "Group normalization" },
        { label: "6", pool: ["unreliable", "slow", "large", "stable"], correct: "unreliable" },
        { label: "7", pool: ["Batch normalization", "Layer normalization", "Instance normalization", "Group normalization"], correct: "Instance normalization" },
        { label: "8", pool: ["Batch normalization", "Layer normalization", "Instance normalization", "Group normalization"], correct: "Batch normalization" },
      ],
      explain: "Batch norm = across the mini-batch (depends on batch size; statistics get unreliable when tiny). Layer norm = per-sample across features. Instance norm = per-channel per-sample. Group norm = groups of channels. Tutor-derived key; blank 4 (features) is the debatable one.",
    },
    // Q7 — MLP backprop derivative matching
    {
      n: 7, type: "dropdown", code: true,
      q: "Hidden layer l with z^(l)=W^(l)a^(l-1)+b^(l), a^(l)=σ(z^(l)), sigmoid σ. The error signal δ^(l) = (∂L/∂z^(l+1))·(∂z^(l+1)/∂a^(l))·(∂a^(l)/∂z^(l)). Match each derivative component to its term.\n\nTERMS  W = W^(l+1) · sig = σ(z^(l))·(1−σ(z^(l))) · delta = δ^(l+1)\n\n∂z^(l+1)/∂a^(l)  =  [[1]]\n∂a^(l)/∂z^(l)   =  [[2]]\n∂L/∂z^(l+1)    =  [[3]]",
      blanks: [
        { label: "∂z^(l+1)/∂a^(l)", pool: ["W", "sig", "delta"], correct: "W" },
        { label: "∂a^(l)/∂z^(l)", pool: ["W", "sig", "delta"], correct: "sig" },
        { label: "∂L/∂z^(l+1)", pool: ["W", "sig", "delta"], correct: "delta" },
      ],
      explain: "z^(l+1)=W^(l+1)a^(l)+b ⇒ ∂z^(l+1)/∂a^(l)=W^(l+1). Sigmoid derivative σ(1−σ). And ∂L/∂z^(l+1) is by definition δ^(l+1). The student swapped W and δ.",
    },
    // Q8 — seq2seq attention vs gating (single)
    {
      n: 8, type: "single",
      q: "Attention and gated recurrence address different but complementary limitations of basic RNN sequence decoding. Which statement is best?",
      options: {
        A: "They are conceptually equivalent (both assign dynamic importance to past info), so a vanilla RNN with attention should match an LSTM without attention on long sequences.",
        B: "Attention removes the need for recurrence by connecting encoder and decoder at every step; gated units mainly improve training stability as a form of regularization.",
        C: "Gated units solve the fixed-context bottleneck by storing the full source history, while attention solves vanishing gradients by controlling recurrent information flow.",
        D: "GRUs/LSTMs guarantee correct alignment between input and output positions, whereas attention guarantees preservation of important past information.",
        E: "Gated recurrence controls how information is updated, retained and forgotten inside the recurrent state across time, whereas attention lets the decoder selectively access relevant encoder states instead of relying on one final summary.",
      },
      correct: "E",
      explain: "E correctly separates the two roles: gating = managing the recurrent state over time (helps vanishing gradients); attention = dynamic access to all encoder states (fixes the single-vector bottleneck). C swaps the two roles.",
    },
    // Q9 — layer normalization numeric
    {
      n: 9, type: "dropdown", code: true,
      q: "Layer-normalize Example 1 = [2, 2, 6, 6]. Use all 4 features, variance = mean squared deviation, ε = 0, γ = 1.5, β = −0.5.\n\nMean:                                   [[1]]\nVariance:                               [[2]]\nNormalized value of the 3rd feature:    [[3]]\nFinal output of the 3rd feature (γ,β):  [[4]]",
      blanks: [
        { label: "mean", pool: ["4", "2", "3", "5"], correct: "4" },
        { label: "variance", pool: ["4", "2", "8", "16"], correct: "4" },
        { label: "norm(3rd)", pool: ["1", "2", "0.5", "-1"], correct: "1" },
        { label: "out(3rd)", pool: ["1.0", "2.0", "0.5", "1.5"], correct: "1.0" },
      ],
      explain: "mean=(2+2+6+6)/4=4. var=((−2)²+(−2)²+2²+2²)/4=4, so std=2. norm of 6 = (6−4)/2 = 1. output = γ·1+β = 1.5−0.5 = 1.0. (Variance is 4, not the std 2 — the common slip.)",
    },
    // Q10 — CNN training code -> line numbers (matching)
    {
      n: 10, type: "dropdown", code: true,
      q: "Match each description to the line number in this CNN training script (lines shown).\n\n 9  self.conv1 = nn.Conv2d(1, 8, kernel_size=3, padding=1)\n10  self.pool  = nn.MaxPool2d(2, 2)\n11  self.fc1   = nn.Linear(8*14*14, 10)\n14  x = self.pool(F.relu(self.conv1(x)))\n15  x = torch.flatten(x, start_dim=1)\n26  optimizer.zero_grad()\n27  outputs = model(images)\n28  loss = criterion(outputs, labels.float())\n29  loss.backward()\n30  optimizer.step()\n\nDefines a convolutional layer that learns local filters   [[1]]\nClears gradients from the previous step                    [[2]]\nLine that raises 'expected scalar type Long but found Float'  [[3]]\nUpdates the model parameters using the gradients           [[4]]\nConverts feature maps into a per-example vector            [[5]]\nReduces the spatial size of the feature maps               [[6]]\nComputes predictions for a batch of images                 [[7]]\nComputes gradients of the loss w.r.t. the parameters       [[8]]",
      blanks: [
        { label: "conv layer", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "9" },
        { label: "clears grads", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "26" },
        { label: "RuntimeError", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "28" },
        { label: "updates params", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "30" },
        { label: "flatten", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "15" },
        { label: "reduces spatial", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "14" },
        { label: "predictions", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "27" },
        { label: "loss gradients", pool: ["9", "10", "14", "15", "26", "27", "28", "29", "30"], correct: "29" },
      ],
      explain: "The error comes from labels.float() — CrossEntropyLoss needs Long class indices (line 28). zero_grad clears (26), backward computes grads (29), step updates (30), model(images) predicts (27), MaxPool reduces spatial size in the forward pass (14), flatten at 15.",
    },
    // Q11 — parameter / memory count (numeric)
    {
      n: 11, type: "dropdown", code: true,
      q: "MLP with layer sizes 8 → 5 → 3 → 2 (each non-input layer has a bias). Count only trainable parameters, their gradients, and optimizer state. Worked check: 4→3→2 gives 23 params and 69 stored values under SGD+momentum (23×3).\n\nTrainable parameters:              [[1]]\nValues stored / iteration, Nesterov:  [[2]]\nValues stored / iteration, Adam:      [[3]]",
      blanks: [
        { label: "params", pool: ["71", "239", "79", "143"], correct: "71" },
        { label: "Nesterov", pool: ["213", "717", "142", "284"], correct: "213" },
        { label: "Adam", pool: ["284", "213", "717", "355"], correct: "284" },
      ],
      explain: "Params = (8·5+5)+(5·3+3)+(3·2+2) = 45+18+8 = 71. Nesterov (1 momentum buffer): params+grads+momentum = 71×3 = 213. Adam (m and v): 71×4 = 284.",
    },
    // Q12 — attentive GRU classifier code (numeric)
    {
      n: 12, type: "dropdown", code: true,
      q: "A many-to-one classifier: input (batch, 5, 8), hidden size 6, 3 output logits, GRU over 5 time steps then attention over all hidden states (H has shape (batch, 5, 6); attn = Linear(6,1)).\n\nNumber of scalar alignment scores per sequence, before softmax:   [[1]]\nNumber of recurrent time steps backprop-through-time passes through:  [[2]]",
      blanks: [
        { label: "alignment scores", pool: ["5", "2", "6", "3"], correct: "5" },
        { label: "BPTT steps", pool: ["5", "3", "6", "8"], correct: "5" },
      ],
      explain: "attn maps each of the 5 hidden states to one scalar ⇒ 5 alignment scores (softmax over the 5). The loop runs 5 steps, so BPTT propagates through all 5.",
    },
    // Q13 — multi-task CustomerNet bugs (multi)
    {
      n: 13, type: "multi",
      q: "A multi-task CustomerNet (shared layer, a classification head, a regression head). Select ALL statements that correctly identify a problem in this code:\n\n  self.shared = nn.Linear(in_features, hidden_dim)\n  self.class_head = nn.Linear(hidden_dim, 1)\n  reg_head = nn.Linear(hidden_dim, 1)\n  ...\n  purchase = torch.sigmoid(self.class_head)\n  spend = self.reg_head(h)",
      options: {
        A: "The classification head is not actually applied to the shared representation h.",
        B: "reg_head is never registered as a module (missing self.), so self.reg_head doesn't exist.",
        C: "self.shared = nn.Linear(...) is invalid because shared layers cannot be used in multi-task networks.",
        D: "torch.sigmoid(self.class_head) is wrong because self.class_head is a layer object, not its output.",
        E: "torch.sigmoid is always wrong for this kind of classification.",
        F: "self.dropout(h) is invalid because dropout can only be used in convolutional networks.",
      },
      correct: ["A", "B", "D"],
      explain: "A and D are the same bug viewed two ways: sigmoid is applied to the layer self.class_head, not to class_head(h). B: reg_head lacks self., so self.reg_head(h) crashes. C, E, F are false. The student caught only B.",
    },
    // Q14 — single-head self-attention code (matching)
    {
      n: 14, type: "dropdown", code: true,
      q: "Single-head self-attention, W_q/W_k/W_v: 8→4, W_o: 4→8, encoder self-attention, no mask. Standard template: q,k,v=W_q(x),W_k(x),W_v(x) → scores=q·kᵀ → /√4 → softmax(dim=-1) → context=attn·v → W_o(context). Classify what each variant does.\n\nLABELS  ok = correct encoder self-attn · maskonly = correct only for masked decoder · swapqk = swaps Q and K roles · shapeC = runtime shape error in context · shapeS = runtime shape error in scores · scale = wrong scaling factor · usev = uses values not keys for scores · reuseq = reuses W_q to make keys · softdim = softmax over wrong dim · noproj = missing output projection\n\nscores = matmul(k, q.transpose(-2,-1))         [[1]]\ncontext = matmul(v, attn_weights)              [[2]]\n(template unchanged, but described as masked decoder self-attn)  [[3]]\nscores = matmul(q, k)   # no transpose         [[4]]\nscores = scores / 4                            [[5]]\nscores = matmul(q, v.transpose(-2,-1))         [[6]]\nk = self.W_q(x)                                [[7]]\nattn_weights = softmax(scores, dim=1)          [[8]]\n(template unchanged)                           [[9]]\noutput = context   # no W_o                    [[10]]",
      blanks: [
        { label: "1", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "swapqk" },
        { label: "2", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "shapeC" },
        { label: "3", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "maskonly" },
        { label: "4", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "shapeS" },
        { label: "5", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "scale" },
        { label: "6", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "usev" },
        { label: "7", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "reuseq" },
        { label: "8", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "softdim" },
        { label: "9", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "ok" },
        { label: "10", pool: ["ok", "maskonly", "swapqk", "shapeC", "shapeS", "scale", "usev", "reuseq", "softdim", "noproj"], correct: "noproj" },
      ],
      explain: "Each variant changes one line of the standard scaled-dot-product template. matmul(q,k) without transpose and matmul(v,attn) are shape errors; /4 instead of /√4 is the scaling bug; softmax(dim=1) attends over the wrong axis; k=W_q(x) reuses the query projection. Tutor-derived key.",
    },
    // Q15 — 3-perceptron step layer (multi)
    {
      n: 15, type: "multi",
      q: "A layer of 3 perceptrons with step activation H(z)=1 if z≥0 else 0, on binary input x=(x1,x2). W rows = [1,0],[1,0],[-1,0]; b = [-0.5,-1.5,2.5]; y=H(W·x+b). Tick ALL output codes (y1,y2,y3) that occur for at least one input.",
      options: {
        A: "(0,0,0)", B: "(0,0,1)", C: "(0,1,0)", D: "(0,1,1)",
        E: "(1,0,0)", F: "(1,0,1)", G: "(1,1,0)", H: "(1,1,1)",
      },
      correct: ["B", "F"],
      explain: "Column for x2 is 0, so x2 is ignored. y1=H(x1−0.5): 0→0, 1→1. y2=H(x1−1.5)=0 always. y3=H(−x1+2.5)=1 always. So x1=0→(0,0,1), x1=1→(1,0,1). Only (0,0,1) and (1,0,1) occur. The student's (0,1,0)/(1,1,0) cannot happen.",
    },
  ];

  const lesson = {
    code: "REAL", id: "real-exam", topic: "Real Exam", title: "Real Exam (transcribed)",
    count: questions.length, real: true, isExam: true,
    source: "Tilburg · Intro to Deep Learning 800883-B-6 · keys tutor-derived",
    questions,
  };

  window.DL_LESSONS = window.DL_LESSONS || [];
  if (!window.DL_LESSONS.some((l) => l.code === "REAL")) window.DL_LESSONS.push(lesson);
})();
