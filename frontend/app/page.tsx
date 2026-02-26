"use client"

import {
  Brain,
  ChevronRight,
  Cpu,
  Database,
  GraduationCap,
  LayoutDashboard,
  Lightbulb,
  LineChart,
  MessageSquare,
  Users,
  Zap,
} from "lucide-react"
import { motion } from "framer-motion"
import Link from "next/link"
import { useEffect, useState } from "react"

// --- Components ---

const HeroSection = () => {
  return (
    <section className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-black px-6 pt-24 text-center md:px-12">
      {/* Background Gradient Orb */}
      <div className="absolute top-[-20%] left-1/2 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-[radial-gradient(circle,rgba(255,106,0,0.15)_0%,rgba(0,0,0,0)_70%)] blur-[100px]" />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="relative z-10 max-w-5xl"
      >
        <h1 className="mb-6 text-5xl font-extrabold tracking-tight text-white md:text-7xl lg:text-8xl">
          <span className="bg-gradient-to-r from-white via-white to-gray-400 bg-clip-text text-transparent">
            SYNERGY OF
          </span>
          <br />
          <span className="bg-gradient-to-r from-[#ff6a00] to-[#ff3c00] bg-clip-text text-transparent">
            MIND & MACHINE
          </span>
        </h1>
        
        <p className="mx-auto mb-8 max-w-2xl text-xl text-gray-400 md:text-2xl">
          Claude Tests — AI that questions your thinking. An adaptive Socratic AI that measures understanding through intelligent questioning.
        </p>
        
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link
            href="/chat"
            className="group relative flex h-12 items-center justify-center overflow-hidden rounded-full bg-[#ff3c00] px-8 font-bold text-white transition-all hover:bg-[#ff6a00] hover:shadow-[0_0_20px_rgba(255,60,0,0.5)]"
          >
            <span className="relative z-10 flex items-center gap-2">
              Start Testing <ChevronRight className="size-4 transition-transform group-hover:translate-x-1" />
            </span>
          </Link>
          <Link
            href="#how-it-works"
            className="group flex h-12 items-center justify-center rounded-full border border-white/10 bg-white/5 px-8 font-medium text-white backdrop-blur-sm transition-all hover:bg-white/10"
          >
            See How It Works
          </Link>
        </div>
      </motion.div>

      {/* Abstract Visual Placeholder */}
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4, duration: 1 }}
        className="relative mt-20 h-64 w-full max-w-4xl"
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative size-64 animate-pulse rounded-full bg-[#ff3c00]/20 blur-3xl" />
          <div className="absolute top-1/2 left-1/2 h-32 w-full -translate-x-1/2 -translate-y-1/2 rounded-[100%] border border-[#ff3c00]/30 bg-black/40 backdrop-blur-xl" />
          <div className="absolute top-1/2 left-1/2 h-full w-32 -translate-x-1/2 -translate-y-1/2 rounded-[100%] border border-[#ff3c00]/30 bg-black/40 backdrop-blur-xl" />
          <div className="absolute top-1/2 left-1/2 size-40 -translate-x-1/2 -translate-y-1/2 rounded-full border border-[#ff3c00]/50 shadow-[0_0_30px_rgba(255,60,0,0.3)]" />
        </div>
      </motion.div>
    </section>
  )
}

const FeatureStrip = () => {
  const features = [
    { title: "Adaptive Questioning", icon: MessageSquare },
    { title: "Knowledge Gap Detection", icon: Zap },
    { title: "Memory Retention Tracking", icon: Database },
    { title: "Difficulty Scaling", icon: LineChart },
    { title: "Cognitive Progress Metrics", icon: Brain },
  ]

  return (
    <div className="w-full border-y border-white/5 bg-black/50 backdrop-blur-sm">
      <div className="flex w-full overflow-hidden py-6">
        <motion.div
          animate={{ x: ["0%", "-50%"] }}
          transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
          className="flex w-max gap-12 px-6"
        >
          {[...features, ...features].map((feature, i) => (
            <div key={i} className="flex items-center gap-3 text-gray-400 transition-colors hover:text-white">
              <feature.icon className="size-5 text-[#ff3c00]" />
              <span className="whitespace-nowrap font-medium tracking-wide uppercase">{feature.title}</span>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  )
}

const AboutSection = () => {
  const cards = [
    {
      title: "Drive Deep Understanding",
      desc: "Forces active recall through guided questions rather than passive reading.",
      icon: Brain,
    },
    {
      title: "Expose Blind Spots",
      desc: "Identifies conceptual weaknesses instantly with precision probing.",
      icon: Lightbulb,
    },
    {
      title: "Strengthen Long-Term Memory",
      desc: "Uses retrieval practice and spaced questioning to lock in knowledge.",
      icon: Database,
    },
    {
      title: "Build Structured Thinking",
      desc: "Trains reasoning and mental models, not just rote memorization.",
      icon: LayoutDashboard,
    },
  ]

  return (
    <section className="bg-black py-32 px-6 text-white md:px-12">
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16 text-center"
        >
          <h2 className="mb-4 text-sm font-bold tracking-[0.2em] text-[#ff3c00] uppercase">The Methodology</h2>
          <h3 className="text-4xl font-bold md:text-5xl">WHY CLAUDE TESTS?</h3>
        </motion.div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {cards.map((card, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-8 transition-all hover:border-[#ff3c00]/50 hover:bg-white/10"
            >
              <div className="mb-6 inline-flex rounded-lg bg-[#ff3c00]/10 p-3 text-[#ff3c00]">
                <card.icon className="size-6" />
              </div>
              <h4 className="mb-3 text-xl font-bold">{card.title}</h4>
              <p className="text-gray-400 leading-relaxed">{card.desc}</p>
              
              {/* Hover Glow */}
              <div className="absolute -right-12 -bottom-12 size-32 rounded-full bg-[#ff3c00]/20 blur-2xl transition-all group-hover:bg-[#ff3c00]/30" />
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

const HowItWorksSection = () => {
  const steps = [
    { num: "01", title: "Explain a Topic", desc: "Start by explaining a concept in your own words." },
    { num: "02", title: "Deep Questioning", desc: "AI asks progressively deeper questions to probe understanding." },
    { num: "03", title: "Adapt & Evaluate", desc: "System evaluates comprehension gaps and adapts difficulty instantly." },
  ]

  return (
    <section id="how-it-works" className="relative border-t border-white/5 bg-black py-32 px-6 text-white md:px-12">
      <div className="absolute top-0 left-0 h-px w-full bg-gradient-to-r from-transparent via-[#ff3c00]/50 to-transparent opacity-30" />
      
      <div className="mx-auto max-w-7xl">
        <div className="mb-20">
          <h2 className="text-4xl font-bold md:text-5xl">HOW IT WORKS</h2>
        </div>

        <div className="grid gap-12 md:grid-cols-3">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.2 }}
              className="relative pl-8"
            >
              <div className="absolute top-0 left-0 h-full w-px bg-white/10">
                <div className="absolute top-0 left-1/2 h-1/2 w-0.5 -translate-x-1/2 bg-gradient-to-b from-[#ff3c00] to-transparent" />
              </div>
              <div className="mb-4 text-6xl font-black text-white/5">{step.num}</div>
              <h3 className="mb-2 text-2xl font-bold">{step.title}</h3>
              <p className="text-gray-400">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

const ServicesSection = () => {
  const cases = [
    { title: "Students", desc: "Preparing for exams & mastering core concepts.", icon: GraduationCap },
    { title: "Engineers", desc: "Understanding complex systems deeply.", icon: Cpu },
    { title: "Founders", desc: "Refining product thinking and strategy.", icon: Lightbulb },
    { title: "Teams", desc: "Training collective knowledge and alignment.", icon: Users },
  ]

  return (
    <section className="bg-[#050505] py-32 px-6 text-white md:px-12">
      <div className="mx-auto max-w-7xl">
        <div className="mb-16 text-center">
          <h2 className="text-3xl font-bold md:text-4xl">BUILT FOR LEARNERS</h2>
        </div>
        
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {cases.map((item, i) => (
            <motion.div
              key={i}
              whileHover={{ y: -5 }}
              className="group flex flex-col items-center rounded-xl border border-white/5 bg-white/[0.02] p-8 text-center transition-colors hover:border-[#ff3c00]/30 hover:bg-white/[0.05]"
            >
              <item.icon className="mb-4 size-8 text-gray-500 transition-colors group-hover:text-[#ff3c00]" />
              <h3 className="mb-2 text-lg font-bold">{item.title}</h3>
              <p className="text-sm text-gray-500 group-hover:text-gray-400">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

const FinalCTASection = () => {
  return (
    <section className="relative overflow-hidden bg-black py-40 px-6 text-center text-white md:px-12">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,60,0,0.1)_0%,rgba(0,0,0,0)_60%)]" />
      
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        className="relative z-10 mx-auto max-w-4xl"
      >
        <h2 className="mb-8 text-5xl font-extrabold tracking-tight md:text-7xl">
          READY TO TEST YOUR
          <br />
          <span className="text-[#ff3c00]">THINKING?</span>
        </h2>
        
        <Link
          href="/chat"
          className="inline-flex h-16 items-center justify-center rounded-full bg-white px-10 text-lg font-bold text-black transition-transform hover:scale-105 hover:bg-gray-100"
        >
          Begin Socratic Session
        </Link>
      </motion.div>
    </section>
  )
}

export default function LandingPage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-black text-white selection:bg-[#ff3c00]/30">
      <HeroSection />
      <FeatureStrip />
      <AboutSection />
      <HowItWorksSection />
      <ServicesSection />
      <FinalCTASection />
      
      <footer className="border-t border-white/10 bg-black py-8 text-center text-sm text-gray-600">
        <p>© {new Date().getFullYear()} Claude Tests. All rights reserved.</p>
      </footer>
    </div>
  )
}
