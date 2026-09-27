import { useRef, useState } from 'react'
import {
  Bone, Cake, Camera, Check, Cookie, House, Pencil, Plus, Ruler, Scale, ShieldCheck, Sparkles, PawPrint,
} from 'lucide-react'
import EditProfileSheet from '../components/EditProfileSheet'
import { SAFETY, TAG_OPTIONS, TRAITS } from '../data'

function ageFrom(birthday) {
  const b = new Date(birthday)
  const now = new Date()
  let years = now.getFullYear() - b.getFullYear()
  if (now < new Date(now.getFullYear(), b.getMonth(), b.getDate())) years--
  return years
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function readImage(file, cb) {
  const reader = new FileReader()
  reader.onload = () => cb(reader.result)
  reader.readAsDataURL(file)
}

function Section({ title, action, children }) {
  return (
    <section className="card">
      <div className="card-head">
        <h3 className="card-title">{title}</h3>
        {action}
      </div>
      {children}
    </section>
  )
}

export default function Profile({ profile, onChange }) {
  const [editing, setEditing] = useState(false)
  const [editTags, setEditTags] = useState(false)
  const photoInput = useRef(null)
  const galleryInput = useRef(null)
  const set = (patch) => onChange({ ...profile, ...patch })
  const age = ageFrom(profile.birthday)

  const toggleTag = (t) =>
    set({ tags: profile.tags.includes(t) ? profile.tags.filter((x) => x !== t) : [...profile.tags, t] })

  return (
    <div className="profile">
      <section className="profile-hero">
        <div className="profile-photo">
          <img src={profile.photo} alt={profile.name} />
          <button className="photo-btn" onClick={() => photoInput.current.click()} aria-label="Change photo">
            <Camera size={17} />
          </button>
          <input
            ref={photoInput} type="file" accept="image/*" hidden
            onChange={(e) => e.target.files[0] && readImage(e.target.files[0], (photo) => set({ photo }))}
          />
        </div>
        <div className="profile-id">
          <div>
            <h1>{profile.name}</h1>
            <p className="profile-breed">{profile.breed} · {age} yrs</p>
          </div>
          <button className="btn-chip" onClick={() => setEditing(true)}>
            <Pencil size={14} /> Edit
          </button>
        </div>
        <p className="profile-tagline">“{profile.tagline}”</p>
      </section>

      <div className="facts">
        <div className="fact"><Cake size={16} /><strong>{age} yrs</strong><span>{formatDate(profile.birthday)}</span></div>
        <div className="fact"><Scale size={16} /><strong>{profile.weight} kg</strong><span>Weight</span></div>
        <div className="fact"><Ruler size={16} /><strong>{profile.size}</strong><span>Size</span></div>
        <div className="fact"><PawPrint size={16} /><strong>{profile.sex}</strong><span>{profile.neutered ? 'Neutered' : 'Intact'}</span></div>
        <div className="fact fact-wide"><Sparkles size={16} /><strong>{profile.coat}</strong><span>Coat</span></div>
      </div>

      <Section
        title="Personality"
        action={
          <button className="link-btn" onClick={() => setEditTags((v) => !v)}>
            {editTags ? <><Check size={14} /> Done</> : <><Pencil size={13} /> Edit</>}
          </button>
        }
      >
        <div className="tags">
          {(editTags ? TAG_OPTIONS : profile.tags).map((t) => (
            <button
              key={t}
              className={`tag ${profile.tags.includes(t) ? 'is-on' : ''}`}
              onClick={() => editTags && toggleTag(t)}
              disabled={!editTags}
            >
              {t}
            </button>
          ))}
        </div>
      </Section>

      <Section title="Temperament">
        <p className="muted small section-hint">Tap a bar to adjust</p>
        <div className="traits">
          {TRAITS.map((t) => {
            const v = profile.traits[t.id]
            return (
              <div key={t.id} className="trait">
                <div className="trait-label">{t.label}</div>
                <div className="meter" role="radiogroup" aria-label={t.label}>
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      className={`seg ${n <= v ? 'is-on' : ''}`}
                      onClick={() => set({ traits: { ...profile.traits, [t.id]: n } })}
                      aria-label={`${t.label} ${n} of 5`}
                    />
                  ))}
                </div>
                <div className="trait-ends"><span>{t.low}</span><span>{t.high}</span></div>
              </div>
            )
          })}
        </div>
      </Section>

      <Section title="Favourites">
        <div className="favs">
          <div className="fav"><Bone size={18} /><span>Toy</span><strong>{profile.favourites.toy}</strong></div>
          <div className="fav"><Cookie size={18} /><span>Treat</span><strong>{profile.favourites.treat}</strong></div>
          <div className="fav"><Sparkles size={18} /><span>Game</span><strong>{profile.favourites.game}</strong></div>
          <div className="fav"><House size={18} /><span>Nap spot</span><strong>{profile.favourites.spot}</strong></div>
        </div>
      </Section>

      <Section title="Fears & triggers">
        <div className="tags">
          {profile.fears.map((f) => <span key={f} className="tag tag-ochre">{f}</span>)}
        </div>
      </Section>

      <Section title="Knows these cues">
        <div className="tags">
          {profile.cues.map((c) => <span key={c} className="tag tag-outline"><Check size={13} /> {c}</span>)}
        </div>
      </Section>

      <Section title={<><ShieldCheck size={14} /> Things Laika should know</>}>
        <p className="muted small section-hint">Laika uses these to keep play gentle and decide what to offer.</p>
        {SAFETY.map((s) => (
          <div key={s.id} className="row">
            <span>{s.label}</span>
            <div className="seg-toggle">
              {[false, true].map((val) => (
                <button
                  key={String(val)}
                  className={profile.safety[s.id] === val ? 'is-on' : ''}
                  onClick={() => set({ safety: { ...profile.safety, [s.id]: val } })}
                >
                  {val ? 'Yes' : 'No'}
                </button>
              ))}
            </div>
          </div>
        ))}
      </Section>

      <Section title="Daily routine">
        <ul className="timeline">
          {profile.routine.map(([time, text]) => (
            <li key={time}><time>{time}</time><span>{text}</span></li>
          ))}
        </ul>
      </Section>

      <Section title="Health">
        {profile.health.map(([k, v]) => (
          <div key={k} className="row"><span className="muted">{k}</span><span>{v}</span></div>
        ))}
      </Section>

      <Section title="Photos">
        <div className="gallery">
          {profile.gallery.map((src, i) => (
            <button key={src + i} className="gallery-item" onClick={() => set({ photo: src })} title="Set as profile photo">
              <img src={src} alt="" />
            </button>
          ))}
          <button className="gallery-add" onClick={() => galleryInput.current.click()} aria-label="Add photo">
            <Plus size={22} />
          </button>
          <input
            ref={galleryInput} type="file" accept="image/*" hidden
            onChange={(e) => e.target.files[0] && readImage(e.target.files[0], (src) => set({ gallery: [...profile.gallery, src] }))}
          />
        </div>
        <p className="muted small section-hint">Tap a photo to make it the profile picture</p>
      </Section>

      {editing && (
        <EditProfileSheet
          profile={profile}
          onClose={() => setEditing(false)}
          onSave={(p) => { onChange(p); setEditing(false) }}
        />
      )}
    </div>
  )
}
