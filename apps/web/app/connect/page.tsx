import type { Metadata } from "next";
import Link from "next/link";
import Boards from "@/components/connect/Boards";
import Hub from "@/components/Hub";
import Private from "@/components/kit/Private";

export const metadata: Metadata = { title: "Connect" };
export default function Page() {
  return (<Hub dest="connect" title="Connect" lead="Peers, mentors and your institution, with your privacy first. Sign-in is required and you appear only under a handle."
    extra={<><p className="mt-6 text-lg"><Link className="text-electric-blue underline" href="/connect/mentors">Mentors</Link> · <Link className="text-electric-blue underline" href="/connect/sessions">Group sessions</Link> · <Link className="text-electric-blue underline" href="/connect/team-strengths">Team strengths map</Link> · <Link className="text-electric-blue underline" href="/connect/feedback">Peer feedback</Link> · <Link className="text-electric-blue underline" href="/practise/cases?pillar=conflict">Team conflict simulator</Link> · <Link className="text-electric-blue underline" href="/connect/mentor-dashboard">Mentor dashboard</Link> · <Link className="text-electric-blue underline" href="/connect/employer">Employer dashboard</Link> · <Link className="text-electric-blue underline" href="/connect/events">Events and competitions</Link> · <Link className="text-electric-blue underline" href="/institution">Your institution</Link></p>
      <h2 className="mb-4 mt-8 text-2xl font-semibold">Community boards</h2><Private why="Community is for signed-in students so conversations stay safe and accountable."><Boards /></Private></>} />);
}
