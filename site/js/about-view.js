// about-view.js — static content, no queries.
export function renderAbout(container) {
  container.innerHTML = `
    <h1>About Groundtruth</h1>
    <p>
      Groundtruth's goal is to consolidate operational and research
      knowledge from volunteer analog space missions — a useful tool for
      future missions preparing to deploy, station managers running these
      programs, and researchers studying the volunteer analog sector as a
      whole.
    </p>
    <p>
      The knowledge already exists, scattered across daily crew reports,
      mission briefs, and post-mission summaries. Groundtruth gives it a
      structured, citable, queryable address.
    </p>
    <p>
      <a href="https://github.com/annsabg/groundtruth" target="_blank" rel="noopener">
        View the repository on GitHub
      </a>
    </p>
    <p>
      Data licensed <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY 4.0</a>.
      Code and schema licensed MIT.
    </p>
  `;
}
