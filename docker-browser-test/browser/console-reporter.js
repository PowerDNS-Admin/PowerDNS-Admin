const fs = require('node:fs');
const path = require('node:path');

class ConsoleReporter {
  constructor(options = {}) {
    this.outputFile = options.outputFile
      || './test-results/browser-console-diagnostics.json';
    this.records = [];
  }

  onTestEnd(test, result) {
    for (const attachment of result.attachments) {
      if (attachment.name !== 'browser-console-diagnostics') {
        continue;
      }

      const contents = attachment.body
        ? attachment.body.toString('utf8')
        : fs.readFileSync(attachment.path, 'utf8');
      this.records.push({
        status: result.status,
        duration_ms: result.duration,
        ...JSON.parse(contents),
      });
    }
  }

  onEnd() {
    const outputPath = path.resolve(this.outputFile);
    const markdownPath = outputPath.replace(/\.json$/, '.md');
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(
      outputPath,
      `${JSON.stringify({ generated_at: new Date().toISOString(), records: this.records }, null, 2)}\n`,
    );

    const lines = [
      '# Browser console diagnostics',
      '',
      '| Project | Browser | Test | Warnings | Errors |',
      '| --- | --- | --- | ---: | ---: |',
    ];
    for (const record of this.records) {
      const warnings = record.diagnostics.filter(
        (entry) => entry.type === 'warning',
      ).reduce((total, entry) => total + entry.count, 0);
      const errors = record.diagnostics.filter(
        (entry) => entry.type === 'error',
      ).reduce((total, entry) => total + entry.count, 0);
      lines.push(
        `| ${record.project} | ${record.browser.family} ${record.browser.version} | ${record.test} | ${warnings} | ${errors} |`,
      );
      for (const entry of record.diagnostics) {
        const message = entry.text
          .replaceAll('|', '\\|')
          .replaceAll('\n', ' ');
        lines.push(
          `| ↳ ${entry.expected ? 'expected ' : ''}${entry.type} ×${entry.count} |  | ${message} (${entry.url}:${entry.line}:${entry.column}) |  |  |`,
        );
      }
    }
    fs.writeFileSync(markdownPath, `${lines.join('\n')}\n`);

    const warningCount = this.records.reduce(
      (count, record) => count + record.diagnostics.filter(
        (entry) => entry.type === 'warning',
      ).reduce((total, entry) => total + entry.count, 0),
      0,
    );
    const errorCount = this.records.reduce(
      (count, record) => count + record.diagnostics.filter(
        (entry) => entry.type === 'error',
      ).reduce((total, entry) => total + entry.count, 0),
      0,
    );
    process.stdout.write(
      `Browser console audit: ${warningCount} warning(s), ${errorCount} error(s). `
      + `Reports: ${outputPath}, ${markdownPath}\n`,
    );
  }
}

module.exports = ConsoleReporter;
