import { Panel, PanelHeader } from './Panel'

export function HelpPanel() {
  return (
    <Panel>
      <PanelHeader title="How this works" />
      <div className="space-y-3 p-4 text-xs leading-relaxed text-[var(--color-text-secondary)]">
        <p>Upload one or more scenes, then ask what you want to know in plain language.</p>
        <p>
          The system figures out the right analysis on its own — object detection, change
          detection, or SAR/optical comparison — based on what you upload and ask.
        </p>
        <p>
          Every result is backed by an execution trace and evidence you can expand, so you can
          verify how the answer was reached.
        </p>
      </div>
    </Panel>
  )
}
