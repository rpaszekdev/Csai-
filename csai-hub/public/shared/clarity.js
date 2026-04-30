/* Microsoft Clarity — session replay + heatmaps. Project: wjswqcotan.
   Single source of truth; all course HTML pages and the React app's
   index.html load this same file via <script src="/shared/clarity.js">. */
(function (c, l, a, r, i, t, y) {
  c[a] =
    c[a] ||
    function () {
      (c[a].q = c[a].q || []).push(arguments);
    };
  t = l.createElement(r);
  t.async = 1;
  t.src = "https://www.clarity.ms/tag/" + i;
  y = l.getElementsByTagName(r)[0];
  y.parentNode.insertBefore(t, y);
})(window, document, "clarity", "script", "wjswqcotan");
