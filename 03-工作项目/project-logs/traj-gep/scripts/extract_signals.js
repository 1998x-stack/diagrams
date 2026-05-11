// Stage 2 — Node wrapper that calls evolver's official extractSignals().
// stdin: JSON {userSnippet, todayLog, recentSessionTranscript, memorySnippet}
// stdout: JSON {signals: [...]}
const path = require('path');
const { extractSignals } = require(
  path.resolve(__dirname, '../../evolver/src/gep/signals.js')
);

let buf = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', (c) => { buf += c; });
process.stdin.on('end', () => {
  let input;
  try {
    input = JSON.parse(buf);
  } catch (e) {
    process.stderr.write('extract_signals.js: invalid JSON on stdin\n');
    process.exit(2);
  }
  try {
    const signals = extractSignals({
      userSnippet:             input.userSnippet || '',
      todayLog:                input.todayLog || '',
      recentSessionTranscript: input.recentSessionTranscript || '',
      memorySnippet:           input.memorySnippet || '',
      recentEvents:            [],
    });
    process.stdout.write(JSON.stringify({ signals }));
  } catch (e) {
    process.stderr.write(`extract_signals.js: ${e.stack || e.message}\n`);
    process.exit(3);
  }
});
