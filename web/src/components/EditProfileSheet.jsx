import { useState } from 'react'
import Sheet from './Sheet'
import { SIZES } from '../data'

export default function EditProfileSheet({ profile, onSave, onClose }) {
  const [draft, setDraft] = useState(profile)
  const set = (patch) => setDraft((d) => ({ ...d, ...patch }))
  const setFav = (k, v) => set({ favourites: { ...draft.favourites, [k]: v } })

  return (
    <Sheet
      title="Edit profile"
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={() => onSave(draft)}>Save</button>
        </>
      }
    >
      <div className="form">
        <label className="input">
          <span>Name</span>
          <input value={draft.name} onChange={(e) => set({ name: e.target.value })} />
        </label>
        <label className="input">
          <span>Breed</span>
          <input value={draft.breed} onChange={(e) => set({ breed: e.target.value })} />
        </label>
        <div className="input-row">
          <label className="input">
            <span>Birthday</span>
            <input type="date" value={draft.birthday} onChange={(e) => set({ birthday: e.target.value })} />
          </label>
          <label className="input">
            <span>Weight (kg)</span>
            <input type="number" min="1" value={draft.weight} onChange={(e) => set({ weight: Number(e.target.value) })} />
          </label>
        </div>

        <div className="input">
          <span>Size</span>
          <div className="seg-toggle seg-full">
            {SIZES.map((s) => (
              <button key={s} className={draft.size === s ? 'is-on' : ''} onClick={() => set({ size: s })}>{s}</button>
            ))}
          </div>
        </div>
        <div className="input-row">
          <div className="input">
            <span>Sex</span>
            <div className="seg-toggle seg-full">
              {['Male', 'Female'].map((s) => (
                <button key={s} className={draft.sex === s ? 'is-on' : ''} onClick={() => set({ sex: s })}>{s}</button>
              ))}
            </div>
          </div>
          <label className="input input-switch">
            <span>Neutered</span>
            <input type="checkbox" className="switch" checked={draft.neutered} onChange={(e) => set({ neutered: e.target.checked })} />
          </label>
        </div>
        <label className="input">
          <span>Coat</span>
          <input value={draft.coat} onChange={(e) => set({ coat: e.target.value })} />
        </label>
        <label className="input">
          <span>Describe {draft.name || 'them'} in a sentence</span>
          <textarea rows="2" value={draft.tagline} onChange={(e) => set({ tagline: e.target.value })} />
        </label>

        <h3 className="form-sub">Favourites</h3>
        <div className="input-row">
          <label className="input"><span>Toy</span><input value={draft.favourites.toy} onChange={(e) => setFav('toy', e.target.value)} /></label>
          <label className="input"><span>Treat</span><input value={draft.favourites.treat} onChange={(e) => setFav('treat', e.target.value)} /></label>
        </div>
        <div className="input-row">
          <label className="input"><span>Game</span><input value={draft.favourites.game} onChange={(e) => setFav('game', e.target.value)} /></label>
          <label className="input"><span>Nap spot</span><input value={draft.favourites.spot} onChange={(e) => setFav('spot', e.target.value)} /></label>
        </div>
      </div>
    </Sheet>
  )
}
