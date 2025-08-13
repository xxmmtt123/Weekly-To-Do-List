from flask import Flask, render_template, redirect, url_for, request, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Integer, String, Boolean, Column, CheckConstraint
from flask_bootstrap import Bootstrap
import csv, io


from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# Config SQLite DB
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(model_class=Base)
db.init_app(app)

def get_current_week_info():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    start_str = start_of_week.strftime('%Y-%m-%d')
    end_str = end_of_week.strftime('%Y-%m-%d')
    week_range = f"{start_str} to {end_str}"

    iso_year, iso_week, _ = today.isocalendar()
    week_index = int(f"{iso_year}{iso_week:02d}")

    return week_range, week_index


def get_next_week_info():
    today = datetime.today()
    start_of_week = today - timedelta(days=today.weekday()) + timedelta(days=7)
    end_of_week = start_of_week + timedelta(days=6)

    start_str = start_of_week.strftime('%Y-%m-%d')
    end_str = end_of_week.strftime('%Y-%m-%d')
    week_range = f"{start_str} to {end_str}"

    iso_year, iso_week, _ = start_of_week.isocalendar()
    week_index = int(f"{iso_year}{iso_week:02d}")

    return week_range, week_index


def get_last_week_info():
    today = datetime.today() - timedelta(weeks=1)

    start_str = today - timedelta(days=today.weekday())
    end_str   = start_str + timedelta(days=6)

    week_range = f"{start_str:%Y-%m-%d} to {end_str:%Y-%m-%d}"

    iso_year, iso_week, _ = start_str.isocalendar()
    week_index = int(f"{iso_year}{iso_week:02d}")

    return week_range, week_index


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    description = Column(String(30), nullable=False)
    done = Column(Boolean, default=False)
    category = Column(String(20), nullable=True)
    week_range = Column(String(50), nullable=False)
    week_index = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("length(description) <= 30", name="ck_tasks_desc_len_le_30"),
    )

# Create DB tables
# with app.app_context():
#     db.create_all()

@app.route("/", methods=['GET','POST'])
def home():
    if request.method == 'POST':
        desc_life = request.form.get('todo_life')
        desc_sport = request.form.get('todo_sport')
        desc_study = request.form.get('todo_study')
        desc_work = request.form.get('todo_work')

        week_range, week_index = get_current_week_info()

        if desc_life:
            if len(desc_life) > 30:
                return redirect(url_for("home"))


            new_task_life = Task(
                description=desc_life,
                category="Life",
                week_range=week_range,
                week_index=week_index
            )
            db.session.add(new_task_life)
            db.session.commit()

        elif desc_sport:
            if len(desc_sport) > 30:
                return redirect(url_for("home"))

            new_task_life = Task(
                description=desc_sport,
                category="Sport",
                week_range=week_range,
                week_index=week_index
            )
            db.session.add(new_task_life)
            db.session.commit()

        elif desc_study:
            if len(desc_study) > 30:
                return redirect(url_for("home"))

            new_task_life = Task(
                description=desc_study,
                category="Study",
                week_range=week_range,
                week_index=week_index
            )
            db.session.add(new_task_life)
            db.session.commit()

        elif desc_work:
            if len(desc_work) > 30:
                return redirect(url_for("home"))

            new_task_life = Task(
                description=desc_work,
                category="Work",
                week_range=week_range,
                week_index=week_index
            )
            db.session.add(new_task_life)
            db.session.commit()
        return redirect(url_for('home'))

    result = db.session.execute(
        db.select(Task)
        .order_by(Task.done.asc())
    )
    tasks = result.scalars().all()
    return render_template("index.html",
                           current_week_range=get_current_week_info()[0],
                           current_week_index=get_current_week_info()[1],
                           tasks=tasks)

@app.route("/delete")
def delete():
    item_id = request.args.get('id')
    item_to_delete = db.session.execute(db.select(Task).where(Task.id == item_id)).scalar()
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/delete_historical/<int:task_id>",methods=['GET','POST'])
def delete_historical(task_id):
    item_to_delete = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar()
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for("historical"))

@app.route("/delete_next/<int:task_id>",methods=['GET','POST'])
def delete_next(task_id):
    item_to_delete = db.session.execute(db.select(Task).where(Task.id == task_id)).scalar()
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for("next_week"))

@app.route("/toggle/<int:item_id>", methods=['GET','POST'])
def toggle(item_id):
    task = db.session.execute(
        db.select(Task).where(Task.id == item_id)
    ).scalar()
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/toggle_historical/<int:task_id>", methods=['GET','POST'])
def toggle_historical(task_id):
    task = db.session.execute(
        db.select(Task).where(Task.id == task_id)
    ).scalar()
    task.done = not task.done
    db.session.commit()
    return redirect(url_for("historical"))


@app.route("/historical", methods=['GET','POST'])
def historical():
    current_week_range, current_week_index = get_current_week_info()

    past_tasks = db.session.execute(
        db.select(Task)
        .where(Task.week_index <= current_week_index)
        .order_by(Task.week_index.desc(), Task.done.asc())
    ).scalars().all()
    return render_template("historical.html",
                           past_tasks=past_tasks)

@app.get("/historical/export")
def export_historical_all():
    _, current_week_index = get_current_week_info()

    rows = db.session.execute(
        db.select(Task)
          .where(Task.week_index <= current_week_index)   # current + past only
          .order_by(Task.week_index.desc(), Task.id.desc())
    ).scalars().all()

    def generate_csv():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        # header
        writer.writerow(["ID","Description","Category","Week Range","Week Index","Done"])
        yield buffer.getvalue(); buffer.seek(0); buffer.truncate(0)
        # rows
        for t in rows:
            writer.writerow([t.id, t.description, t.category, t.week_range, t.week_index, t.done])
            yield buffer.getvalue(); buffer.seek(0); buffer.truncate(0)

    filename = f"tasks_historical_{datetime.now():%Y%m%d}.csv"
    return Response(generate_csv(),
                    mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.route("/next_week", methods=['GET','POST'])
def next_week():
    current_week_range, current_week_index = get_current_week_info()
    next_week_range, next_week_index = get_next_week_info()

    if request.method == 'POST':
        desc_life = request.form.get('todo_life')
        desc_sport = request.form.get('todo_sport')
        desc_study = request.form.get('todo_study')
        desc_work = request.form.get('todo_work')

        if desc_life:
            if len(desc_life) > 30:
                return redirect(url_for("next_week"))


            new_task_life = Task(
                description=desc_life,
                category="Life",
                week_range=next_week_range,
                week_index=next_week_index
            )
            db.session.add(new_task_life)
            db.session.commit()

        elif desc_sport:
            if len(desc_sport) > 30:
                return redirect(url_for("next_week"))

            new_task_life = Task(
                description=desc_sport,
                category="Sport",
                week_range=next_week_range,
                week_index=next_week_index
            )
            db.session.add(new_task_life)
            db.session.commit()

        elif desc_study:
            if len(desc_study) > 30:
                return redirect(url_for("next_week"))

            new_task_life = Task(
                description=desc_study,
                category="Study",
                week_range=next_week_range,
                week_index=next_week_index
            )
            db.session.add(new_task_life)
            db.session.commit()

        elif desc_work:
            if len(desc_work) > 30:
                return redirect(url_for("next_week"))

            new_task_life = Task(
                description=desc_work,
                category="Work",
                week_range=next_week_range,
                week_index=next_week_index
            )
            db.session.add(new_task_life)
            db.session.commit()
        return redirect(url_for('next_week'))

    next_week_tasks = db.session.execute(
        db.select(Task)
        .where(Task.week_index > current_week_index)
        .order_by(Task.week_index.desc(), Task.done.asc())
    ).scalars().all()
    return render_template("next.html",
                           next_week_tasks=next_week_tasks,
                           next_week_range=next_week_range)

@app.post("/copy_last_week")
def copy_last_week():
    current_range, current_index = get_current_week_info()
    last_range, last_index       = get_last_week_info()

    last_tasks = db.session.execute(
        db.select(Task).where(Task.week_index == last_index)
    ).scalars().all()
    if not last_tasks:
        return redirect(request.referrer or url_for("home"))
    # If it’s empty, the code sends the user back to where they came from (request.referrer) or, if there’s no referrer, sends them to the "home" page.

    # Build set of (description, category) already in current week
    existing_pairs = set(
        db.session.execute(
            db.select(Task.description, Task.category).where(Task.week_index == current_index)
        ).all()
    )

    created = 0
    for t in last_tasks:
        key = (t.description, t.category)
        if key in existing_pairs:
            continue
        db.session.add(Task(
            description=t.description,
            category=t.category,
            done=False,
            week_range=current_range,
            week_index=current_index
        ))
        created += 1

    db.session.commit()
    return redirect(request.referrer or url_for("home"))

if __name__ == '__main__':
    app.run(debug=True)