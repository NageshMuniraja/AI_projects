const { Client } = require('pg');
require('dotenv').config({ path: require('path').join(__dirname, '../../.env') });

async function seedDatabase() {
  const client = new Client({
    connectionString: process.env.DATABASE_URL,
  });

  try {
    console.log('Connecting to database...');
    await client.connect();
    console.log('✓ Connected successfully');

    console.log('\nSeeding database with sample data...');

    // Sample user (you'll need to get real Clerk user ID after signup)
    await client.query(`
      INSERT INTO users (clerk_user_id, email, full_name)
      VALUES 
        ('user_sample123', 'demo@example.com', 'Demo User')
      ON CONFLICT (clerk_user_id) DO NOTHING;
    `);
    console.log('✓ Sample user created');

    // Sample team
    await client.query(`
      INSERT INTO teams (name, slug, plan)
      VALUES ('Demo Company', 'demo-company', 'pro')
      ON CONFLICT (slug) DO NOTHING;
    `);
    console.log('✓ Sample team created');

    // Get IDs for relationships
    const userResult = await client.query(`SELECT id FROM users WHERE email = 'demo@example.com'`);
    const teamResult = await client.query(`SELECT id FROM teams WHERE slug = 'demo-company'`);
    
    if (userResult.rows.length > 0 && teamResult.rows.length > 0) {
      const userId = userResult.rows[0].id;
      const teamId = teamResult.rows[0].id;

      // Sample team member
      await client.query(`
        INSERT INTO team_members (team_id, user_id, role)
        VALUES ($1, $2, 'owner')
        ON CONFLICT (team_id, user_id) DO NOTHING;
      `, [teamId, userId]);
      console.log('✓ Team member added');

      // Sample invoices
      await client.query(`
        INSERT INTO invoices (team_id, invoice_number, vendor_name, amount, currency, issue_date, due_date, status)
        VALUES 
          ($1, 'INV-001', 'Acme Corp', 5000.00, 'USD', CURRENT_DATE - 30, CURRENT_DATE - 5, 'overdue'),
          ($1, 'INV-002', 'TechSupplies Inc', 2500.00, 'USD', CURRENT_DATE - 15, CURRENT_DATE + 15, 'pending'),
          ($1, 'INV-003', 'Cloud Services Ltd', 1200.00, 'USD', CURRENT_DATE - 60, CURRENT_DATE - 30, 'paid')
        ON CONFLICT (invoice_number) DO NOTHING;
      `, [teamId]);
      console.log('✓ Sample invoices created');

      // Sample leads
      await client.query(`
        INSERT INTO leads (team_id, email, full_name, company, role, industry, score, priority, status)
        VALUES 
          ($1, 'john@techcorp.com', 'John Smith', 'TechCorp Inc', 'CTO', 'technology', 85, 'high', 'qualified'),
          ($1, 'sarah@startup.io', 'Sarah Johnson', 'Startup.io', 'CEO', 'technology', 72, 'medium', 'contacted'),
          ($1, 'mike@enterprise.com', 'Mike Brown', 'Enterprise Co', 'VP Sales', 'finance', 65, 'medium', 'new')
        ON CONFLICT DO NOTHING;
      `, [teamId]);
      console.log('✓ Sample leads created');

      // Sample agent actions
      await client.query(`
        INSERT INTO agent_actions (team_id, agent_type, action_type, status, confidence_score)
        VALUES 
          ($1, 'finance', 'invoice_reminder_sent', 'executed', 0.95),
          ($1, 'sales', 'lead_scored', 'executed', 0.92),
          ($1, 'reporting', 'daily_summary_generated', 'executed', 1.00)
        ON CONFLICT DO NOTHING;
      `, [teamId]);
      console.log('✓ Sample agent actions logged');
    }

    console.log('\n✓ Database seeded successfully!');

  } catch (error) {
    console.error('\n✗ Seeding failed:', error.message);
    process.exit(1);
  } finally {
    await client.end();
    console.log('\nDatabase connection closed.');
  }
}

seedDatabase();
