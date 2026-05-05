import type { CheckerStatus } from '../types'
import './UpdateCard.css'

interface Props {
  checker: CheckerStatus
}

export function UpdateCard({ checker }: Props) {
  return (
    <div className={`update-card ${checker.error ? 'card-error' : checker.update_available ? 'card-updates' : 'card-ok'}`}>
      <div className="card-header">
        <h2 className="card-title">{checker.type}</h2>
        <span className={`badge ${checker.error ? 'badge-error' : checker.update_available ? 'badge-updates' : 'badge-ok'}`}>
          {checker.error ? 'Error' : checker.update_available ? `${checker.updates.length} update${checker.updates.length !== 1 ? 's' : ''}` : 'Up to date'}
        </span>
      </div>

      {checker.error && (
        <p className="card-error-message">{checker.error}</p>
      )}

      {!checker.error && !checker.update_available && (
        <div className="card-ok-icon">✓</div>
      )}

      {checker.updates.length > 0 && (
        <ul className="update-list">
          {checker.updates.map((u) => (
            <li key={u.name} className="update-item">
              <span className="update-name">{u.name}</span>
              <span className="update-versions">
                <span className="version-current">{u.current_version}</span>
                <span className="version-arrow">→</span>
                <span className="version-new">{u.new_version}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
