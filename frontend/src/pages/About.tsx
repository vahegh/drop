import { Link } from 'react-router-dom'
import { useMe } from '../hooks/useMe'
import Layout from '../components/Layout'
import Section from '../components/Section'
import { loginUrl } from '../lib/loginUrl'

export default function About() {
  const { data: me } = useMe()

  return (
    <Layout showFooter>
      <Section className="pt-6">
        <h1 className="text-3xl font-bold text-center">About Us</h1>
      </Section>

      <Section sep>
        <div className="text-sm text-white/80 leading-relaxed w-full flex flex-col gap-4">
          <p>
            <strong>Drop Dead Disco</strong> is a dance music community for those who want more from a night out.
          </p>
          <p>
            We host our events in unexpected locations — whatever has the most sparkle.
          </p>
          <p>
            We don't tell you the location beforehand, and every guest has to pass <strong>verification</strong> before they're able to buy tickets and attend.
          </p>
        </div>
      </Section>

      <Section title="Verification?" sep>
        <div className="text-sm text-white/80 leading-relaxed w-full flex flex-col gap-4">
          <p>Yes.</p>
          <p>
            The reason we started this was to gather like-minded people around the thing we love the most — <strong>music</strong>.
            We want to make sure that everyone gets that. Thus, we are very strict about who we let in.
          </p>
          <p>
            We review you through your Instagram account. We don't share your information.
            Once you've become a regular and proven to be a part of the community, we may invite you to become a <strong>Member</strong>.
          </p>
        </div>
      </Section>

      <Section title="Who are the Members?" sep>
        <div className="text-sm text-white/80 leading-relaxed w-full flex flex-col gap-4">
          <p>
            <strong>Members</strong> are the heart and soul of Drop Dead Disco — without them this couldn't happen.
            As such, they get more benefits like:
          </p>
          <ul className="list-disc list-inside flex flex-col gap-1 text-white/70">
            <li>Discounted event access</li>
            <li>Special digital cards with their serial no. and number of events attended</li>
            <li>Member-only events</li>
          </ul>
        </div>
      </Section>

      <Section title="What to expect?" sep>
        <div className="text-sm text-white/80 leading-relaxed w-full flex flex-col gap-4">
          <p>First, the location will be revealed 24h before the start of the event, only to members and ticket holders.</p>
          <p>It's likely that it will be your first time there, and that you'll love it.</p>
          <p>Almost certainly, you'll meet some people who you'll connect with, and want to keep in touch.</p>
          <p>You'll hear some of your favourite tracks (even ones you had forgotten about), and some new bangers.</p>
        </div>
      </Section>

      {!me && (
        <>
          <Section title="How do I get in?" sep>
            <div className="text-sm text-white/80 leading-relaxed w-full flex flex-col gap-3">
              <ol className="list-decimal list-inside flex flex-col gap-2 text-white/70">
                <li>Tap the button below and sign up.</li>
                <li>As soon as you sign up, we get notified and the review process begins.</li>
                <li>You'll be notified about your status in 24 hours. If verified, you'll be able to buy tickets for upcoming events.</li>
              </ol>
              <p className="text-white/60">
                If there are no planned events at the time of your approval, you're still in, and will get future event updates as they are available.
              </p>
            </div>
          </Section>

          <Section title="Wanna join the fun?" subtitle="Sign up to get verified" sep>
            <a href={loginUrl('/')} className="btn-primary">
              <img src="/static/images/google.svg" alt="" className="w-4 h-4 mr-2" />
              Sign up with Google
            </a>
          </Section>
        </>
      )}

      <Section sep className="pb-4">
        <Link to="/" className="btn-outline">← Home</Link>
      </Section>
    </Layout>
  )
}
